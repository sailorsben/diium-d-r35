"""Exercise full readback through independent SPI packets and native/ARM execution."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, re, shutil, subprocess, tempfile, zlib
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/spi-readback-out'


def linux(path):
    path = Path(path).resolve()
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def wsl(args, **kwargs):
    return subprocess.run(['wsl', '--exec', *map(str, args)], check=True, **kwargs)


def run():
    wsl(['sh', linux(ROOT / 'build/build-spi-readback.sh')])
    spec = importlib.util.spec_from_file_location('readback_manager', ROOT / 'build/manage-spi-readback.py')
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)
    checks = []
    with tempfile.TemporaryDirectory(prefix='readback-check-', dir=OUT) as name:
        temp = Path(name)
        harness = temp / 'harness.c'
        harness.write_text(r'''
static unsigned long long fixture_deadline_ns=10000000000ull;
#define READBACK_DEADLINE_NS fixture_deadline_ns
#define ioctl fixture_ioctl
#define lstat64 fixture_lstat64
#define fstat64 fixture_fstat64
#define __lxstat64 fixture_lxstat64
#define __fxstat64 fixture_fxstat64
#define opendir fixture_opendir
#define main reader_main
#include "spi-readback.c"
#undef main
#undef ioctl
#undef lstat64
#undef fstat64
#undef __lxstat64
#undef __fxstat64
#undef opendir
#include <stdarg.h>
#include <assert.h>
extern DIR *opendir(const char *);
static unsigned scenario,reads,settings;
static int suffix(const char *s,const char *end) { return strlen(s)>=strlen(end)&&!strcmp(s+strlen(s)-strlen(end),end); }
DIR *fixture_opendir(const char *path) {
    if(scenario==10&&suffix(path,"/proc")) { struct timespec t={3,0};syscall(SYS_nanosleep,&t,NULL); }
    return opendir(path);
}
static void node(struct stat64 *s) { memset(s,0,sizeof(*s));s->st_mode=S_IFCHR|0600;s->st_rdev=makedev(153,0); }
int fixture_lstat64(const char *p,struct stat64 *s) { assert(suffix(p,"/dev/spidev0.0"));node(s);return 0; }
int fixture_fstat64(int fd,struct stat64 *s) { (void)fd;node(s);return 0; }
int fixture_lxstat64(int version,const char *p,struct stat64 *s) { assert(version==3);return fixture_lstat64(p,s); }
int fixture_fxstat64(int version,int fd,struct stat64 *s) { assert(version==3);return fixture_fstat64(fd,s); }
int fixture_ioctl(int fd,unsigned long request,...) {
    (void)fd;va_list args;va_start(args,request);void *value=va_arg(args,void *);va_end(args);
    if(request==SPI_IOC_RD_MODE32) { *(uint32_t*)value=SPI_RX_DUAL;return 0; }
    if(request==SPI_IOC_RD_BITS_PER_WORD) { *(unsigned char*)value=8;return 0; }
    if(request==SPI_IOC_RD_MAX_SPEED_HZ) { settings++;*(uint32_t*)value=scenario==9&&settings>2?19000000:20000000;return 0; }
    assert(request==0x40406b00ul);struct spi_ioc_transfer *x=value;
    assert(x[0].tx_buf&&x[0].rx_buf==0&&x[0].speed_hz==1000000&&x[0].bits_per_word==8&&x[0].tx_nbits==1);
    assert(x[1].tx_buf==0&&x[1].rx_buf&&x[1].speed_hz==1000000&&x[1].bits_per_word==8&&x[1].rx_nbits==1);
    assert(!x[0].cs_change&&!x[1].cs_change&&!x[0].delay_usecs&&!x[1].delay_usecs);
    assert(!x[0].rx_nbits&&!x[1].tx_nbits&&!x[0].pad&&!x[1].pad);
    unsigned char *command=(void*)(uintptr_t)x[0].tx_buf,*out=(void*)(uintptr_t)x[1].rx_buf;
    if(command[0]==5) { assert(x[0].len==1&&x[1].len==1);out[0]=scenario==8?1:0; }
    else if(command[0]==0x9f) {
        const unsigned char id[]={0xc8,0x40,0x17,0xc8,0x40,0x17};
        assert(x[0].len==1&&x[1].len==6);memcpy(out,id,6);if(scenario==7)out[0]=0xef;
    } else {
        assert(command[0]==3&&x[0].len==4&&x[1].len==4096);
        unsigned address=((unsigned)command[1]<<16)|((unsigned)command[2]<<8)|command[3];
        assert(address==(reads%2048)*4096&&address<=0x7ff000);
        if(scenario==5)return 4;
        if(scenario==6) { errno=EIO;return -1; }
        for(unsigned i=0;i<4096;i++) {
            unsigned a=address+i;out[i]=(unsigned char)((a*29u)^(a>>8)^(a>>16)^(a>>23));
        }
        if(scenario==2&&reads==2048)out[99]^=1;
        if(scenario==3)memset(out,0xff,4096);
        if(scenario==4)memset(out,0,4096);
        if(scenario==11)memset(out,0xa5,4096);
        reads++;
    }
    return (int)(x[0].len+x[1].len);
}
int main(int argc,char **argv) {
    assert(argc==4);scenario=pid_number(argv[1]);
    char report_path[PATH_MAX],bundle_path[PATH_MAX];
    if(scenario==10||scenario==12) {
        if(scenario==10)fixture_deadline_ns=100000000ull;
        char *a[]={argv[0],argv[2],argv[3]};return reader_main(3,a);
    }
    snprintf(root,sizeof(root),"%s",argv[2]);assert(!mkdir(argv[3],0700));
    snprintf(report_path,sizeof(report_path),"%s/report.jsonl",argv[3]);
    snprintf(bundle_path,sizeof(bundle_path),"%s/captures.bin",argv[3]);
    FILE *report=fopen(report_path,"wx");assert(report);
    int bundle=open(bundle_path,O_RDWR|O_CREAT|O_EXCL,0600);assert(bundle>=0);
    fprintf(report,"{\"kind\":\"start\",\"version\":1,\"expected_jedec\":\"c84017\",\"capacity_bytes\":8388608,\"passes\":2}\n");
    Snapshot s={0};snapshot(bundle,report,&s);
    const int expected[]={0,0,EILSEQ,ENODATA,ENODATA,EIO,EIO,ENODEV,EBUSY,ESTALE,ETIMEDOUT,ENODATA};
    assert(scenario<12&&s.chip.error==expected[scenario]);
    if(scenario==1)assert(reads==4096&&s.compared&&s.bytes[0]==8388608&&s.bytes[1]==8388608&&s.crc[0]==s.crc[1]&&s.chip.operations==4111);
    assert(!summary(report,&s,0,0));assert(!fclose(report)&&!close(bundle));return 0;
}
''', encoding='utf-8', newline='\n')
        common = ['-std=gnu99', '-O2', '-Wall', '-Wextra', '-Werror', '-Wno-format-truncation', '-I' + linux(ROOT / 'build')]
        wsl(['gcc', *common, linux(harness), '-o', linux(temp / 'native')])
        wsl(['arm-linux-gnueabihf-gcc', '-mcpu=cortex-a7', '-mfpu=neon-vfpv4', '-mfloat-abi=hard', '-marm',
            '-U_TIME_BITS', '-D_TIME_BITS=32', '-U_FILE_OFFSET_BITS', '-D_FILE_OFFSET_BITS=32', *common,
            '-no-pie', '-nostdlib', '/usr/arm-linux-gnueabihf/lib/crt1.o', linux(harness),
            '-L' + linux(ROOT / 'build/sysroot/lib'), '-Wl,--no-as-needed', '-l:libc-2.30.so', '-l:libgcc_s.so.1', '-l:ld-2.30.so', '-o', linux(temp / 'arm')])
        fixture = temp / 'root'
        (fixture / 'proc').mkdir(parents=True)
        (fixture / 'dev').mkdir()
        (fixture / 'dev/spidev0.0').write_bytes(b'No real SPI device; metadata and ioctl are independent fixtures')
        success = None
        for label, executable in [('native', [linux(temp / 'native')]), ('arm', ['qemu-arm', '-cpu', 'cortex-a7', '-L', linux(ROOT / 'build/sysroot'), linux(temp / 'arm')])]:
            for scenario in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12]:
                base = temp / (label + '-' + str(scenario))
                base.mkdir()
                wsl([*executable, str(scenario), linux(fixture), linux(base / 'results')], stdout=subprocess.DEVNULL)
                (base / 'installation.json').write_text('{"run_id":"independent-marker"}')
                (base / 'consumed').write_text('independent-marker\n')
                (base / 'startup.log').write_text('readback_exit=0\n')
                analyzed = manager.analyze(base)
                assert analyzed['complete'] == (scenario in [1, 12]), (label, scenario, analyzed)
                if scenario in [1, 12]:
                    success = base
                    data = (base / 'results/captures.bin').read_bytes()
                    assert data[:8388608] == data[8388608:]
                    assert analyzed['result']['crc32'] == [f'{zlib.crc32(data[:8388608]):08x}'] * 2
            checks.append(label + ': independent 03/address/4096-byte packet contract; full supervised two-pass capture/CRC; mismatch/blank/floating/short/error/wrong-ID/busy/settings-change refusals')
            timed = temp / (label + '-timeout')
            p = subprocess.run(['wsl', '--exec', *executable, '10', linux(fixture), linux(timed)])
            end = json.loads((timed / 'report.jsonl').read_text().splitlines()[-1])
            assert p.returncode == 1 and end['timed_out'] and not end['reap_pending']
            checks.append(label + ': actual owned-child deadline, SIGKILL and reap')
        # Alter real returned bytes rather than manufacturing a matching summary.
        data = (success / 'results/captures.bin').read_bytes()
        (success / 'results/captures.bin').write_bytes(data[:-1])
        assert not manager.analyze(success)['complete']
        (success / 'results/captures.bin').write_bytes(data[:8388608] + bytes([data[8388608] ^ 1]) + data[8388609:])
        assert not manager.analyze(success)['complete']
        (success / 'results/captures.bin').write_bytes(data)
        (success / 'consumed').write_text('stale-id\n')
        assert not manager.analyze(success)['complete']
        (success / 'consumed').write_text('independent-marker\n')
        assert manager.analyze(success)['complete']
        checks.append('return analyzer rejects torn bundle, changed bytes and stale marker')
        archive = temp / 'unhealthy-restore'
        archive.mkdir()
        shutil.copytree(success, archive / 'spi-readback')
        (fixture / 'retro/spi-readback').mkdir(parents=True)
        class Survey:
            @staticmethod
            def healthy():
                raise AssertionError('independent unhealthy FAT fixture')
        original = manager.baseline
        manager.baseline = lambda *args: archive
        try:
            manager.collect(fixture, object(), Survey(), True)
            raise AssertionError('Unhealthy restoration accepted')
        except AssertionError as e:
            assert str(e) == 'independent unhealthy FAT fixture'
        finally:
            manager.baseline = original
        assert (archive / 'readback-analysis.json').exists()
        checks.append('restoration archives analysis and refuses unhealthy FAT before mutation')
        (fixture / 'proc/44/fd').mkdir(parents=True)
        wsl(['ln', '-s', '/dev/spidev0.0', linux(fixture / 'proc/44/fd/8')])
        refused = temp / 'release-refusal'
        p = subprocess.run(['wsl', '--exec', 'qemu-arm', '-cpu', 'cortex-a7', '-L', linux(ROOT / 'build/sysroot'), linux(OUT / 'spi-readback'), linux(fixture), linux(refused)])
        result = json.loads((refused / 'report.jsonl').read_text().splitlines()[-1])
        assert p.returncode == 1 and result['owner_pid'] == 44 and result['operations'] == 0
        checks.append('exact release ARM binary refuses existing owner without opening SPI')
        busybox = ROOT / 'device-evidence/snes-mvp-return-20261009T165057Z/vesper-boot-probe/results/busybox'
        wrapper = temp / 'wrapper'
        wrapper.mkdir()
        (wrapper / 'armed').write_text('independent-id\n')
        (wrapper / 'spi-readback').write_text('#!/bin/sh\nprintf read-only-fixture\n', newline='\n')
        wsl(['chmod', '+x', linux(wrapper / 'spi-readback')])
        tools_dir = temp / 'tools'
        tools_dir.mkdir()
        for name in ['mv', 'sync']:
            wsl(['ln', '-s', '/bin/' + name, linux(tools_dir / name)])
        call = ['env', 'PATH=' + linux(tools_dir), 'D35_READBACK_BASE=' + linux(wrapper), 'D35_READBACK_ROOT=' + linux(fixture),
                '/usr/bin/qemu-arm', '-cpu', 'cortex-a7', '-L', linux(ROOT / 'build/sysroot'), linux(busybox), 'sh', linux(ROOT / 'build/launch-spi-readback.sh')]
        wsl(call)
        assert not (wrapper / 'armed').exists() and (wrapper / 'consumed').read_text() == 'independent-id\n'
        before = (wrapper / 'startup.log').read_bytes()
        wsl(call)
        assert (wrapper / 'startup.log').read_bytes() == before
        checks.append('actual firmware BusyBox consume-first synchronous wrapper and next-boot no-op')
    versions = re.findall(r'Name: GLIBC_([0-9.]+)', (OUT / 'abi.txt').read_text())
    assert versions and all(tuple(map(int, v.split('.'))) <= (2, 30) for v in versions)
    checks.append('exact ARM GLIBC dependencies <= 2.30')
    release = ROOT / 'releases/spi-readback-1'
    release.mkdir(exist_ok=True)
    qualification = {'software_checks_passed': True, 'checks': checks, 'physical_execution': 'pending'}
    (OUT / 'qualification.json').write_text(json.dumps(qualification, indent=2) + '\n', newline='\n')
    for path, name in [(OUT / 'spi-readback', 'spi-readback'), (OUT / 'abi.txt', 'abi.txt'), (OUT / 'qualification.json', 'qualification.json'), (ROOT / 'build/launch-spi-readback.sh', 'launch.sh')]:
        shutil.copyfile(path, release / name)
    names = ['build/spi-readback.c', 'build/spi-identify.c', 'build/build-spi-readback.sh', 'build/launch-spi-readback.sh',
             'build/check-spi-readback.py', 'build/manage-spi-readback.py', 'build/manage-spi-identify.py', 'build/manage-device-survey.py']
    manifest = {'version': 1, 'physical_execution': 'pending', 'software_checks_passed': True,
        'fixed_commands': ['05', '9f', '03'], 'flash_writes': False, 'global_config_writes': False,
        'source_hashes': {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in names},
        'release_hashes': {name: sha256((release / name).read_bytes()).hexdigest() for name in ['spi-readback', 'abi.txt', 'qualification.json', 'launch.sh']}}
    (release / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', newline='\n')
    print(json.dumps({'passed_checks': len(checks), 'physical_execution': 'pending', 'release': str(release)}, indent=2))


if __name__ == '__main__':
    run()
