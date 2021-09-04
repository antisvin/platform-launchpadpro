from os.path import join
from SCons.Script import AlwaysBuild, Builder, Default, DefaultEnvironment


env = DefaultEnvironment()

PLATFORM_DIR = env.PioPlatform().get_dir()

env.Replace(
    CC='arm-none-eabi-gcc',
    CXX='arm-none-eabi-g++',
    OBJCOPY='arm-none-eabi-objcopy',
    LDSCRIPT_PATH=join(PLATFORM_DIR, 'ld/stm32_flash.ld'),
    CFLAGS=[
        '-Os',
        '-Wall',
        '-D_STM32F103RBT6_',
        '-D_STM3x_',
        '-D_STM32x_',
        '-mthumb',
        '-mcpu=cortex-m3',
        '-fsigned-char',
        '-finline-small-functions',
        '-findirect-inlining',
        '-DSTM32F10X_MD',
        '-DUSE_STDPERIPH_DRIVER',
        '-DHSE_VALUE=6000000UL',
        '-DCMSIS',
        '-DUSE_GLOBAL_CONFIG',
        '-ffunction-sections',
        '-std=c99',
        '-mlittle-endian'
    ],
    CPPFLAGS=[
        '-Os',
        '-Wall',
        '-D_STM32F103RBT6_',
        '-D_STM3x_',
        '-D_STM32x_',
        '-mthumb',
        '-mcpu=cortex-m3',
        '-fsigned-char',
        '-finline-small-functions',
        '-findirect-inlining',
        '-DSTM32F10X_MD',
        '-DUSE_STDPERIPH_DRIVER',
        '-DHSE_VALUE=6000000UL',
        '-DCMSIS',
        '-DUSE_GLOBAL_CONFIG',
        '-ffunction-sections',
        '-std=c++17',
        '-ffreestanding',
        '-fno-exceptions',
        '-fno-non-call-exceptions',
        '-fno-rtti',
        '-fno-common',
        '-fdata-sections',
        '-mlittle-endian'
    ],
    LINKFLAGS=[
        '-u',
        '_start',
        '-u',
        '_Minimum_Stack_Size',
        '-mcpu=cortex-m3',
        '-mthumb',
        '-specs=nano.specs',
        '-specs=nosys.specs',
        '-nostdlib',
        '-Wl,-static',
        '-N',
        '-nostartfiles',
        '-Wl,--gc-sections'
    ],
    PROGNAME='launchpad_pro',
    HEXTOSYX=join(PLATFORM_DIR, 'tools/hextosyx.py'),
    SENDSYSEX=join(PLATFORM_DIR, 'tools/sendsysex.py'),
)

env.Append(
    LIBS=[
        File(join(PLATFORM_DIR, 'lib/launchpad_pro.a'))
    ],
    CPPPATH=[
        join(PLATFORM_DIR, 'include')
    ],
)

env.Append(
    BUILDERS=dict(
        ElfToHex=Builder(
            action=env.VerboseAction(' '.join([
                '$OBJCOPY',
                '-O',
                'ihex',
                '$SOURCES',
                '$TARGET'
            ]), 'Building $TARGET'),
            suffix='.hex'
        ),
        HexToSyx=Builder(
            action=env.VerboseAction(' '.join([
                'python3',
                '$HEXTOSYX',
                '$SOURCES',
                '$TARGET'
            ]), 'Building $TARGET'),
            suffix='.syx'
        ),
    ),
)

# Target: Build

if 'nobuild' in COMMAND_LINE_TARGETS:
    target_elf = join('$BUILD_DIR', '${PROGNAME}.elf')
    target_hex = join('$BUILD_DIR', '${PROGNAME}.hex')
    target_syx = join('$BUILD_DIR', '${PROGNAME}.syx')
else:
    target_elf = env.BuildProgram()
    target_hex = env.ElfToHex(join('$BUILD_DIR', '${PROGNAME}'), target_elf)
    target_syx = env.HexToSyx(join('$BUILD_DIR', '${PROGNAME}'), target_hex)

AlwaysBuild(env.Alias('nobuild', target_syx))

# Target: Print binary size

env.Replace(
    SIZETOOL='arm-none-eabi-size',
    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',
)

target_size = env.Alias(
    'size',
    target_elf,
    env.VerboseAction('$SIZEPRINTCMD', 'Calculating size $SOURCE'),
)

AlwaysBuild(target_size)

# Target: Upload

env.Replace(
    UPLOAD_PORT='"Launchpad Pro"'
)

upload = env.VerboseAction(' '.join([
    'python3',
    '$SENDSYSEX',
    '-p',
    '$UPLOAD_PORT',
    '$SOURCE'
]), 'Uploading $SOURCE')

env.AddPlatformTarget(
    'upload',
    target_syx,
    upload,
    'Upload',
    'Send firmware to Launchpad Pro over MIDI',
)

# Target: Restore

env.AddPlatformTarget(
    'restore',
    join(PLATFORM_DIR, 'resources/Launchpad Pro.syx'),
    upload,
    'Restore',
    'Restore Launchpad Pro original firmware',
)

# Default Targets

Default([target_syx, target_size])
