# MPV_BD

[![Build](https://img.shields.io/github/actions/workflow/status/miaminlk/MPV_BD/mpv.yml?branch=main)](https://github.com/miaminlk/MPV_BD/actions)
[![Release](https://img.shields.io/github/v/release/miaminlk/MPV_BD)](https://github.com/miaminlk/MPV_BD/releases/latest)

基于 [zhongfly/mpv-winbuild](https://github.com/zhongfly/mpv-winbuild) 和 [shinchiro/mpv-winbuild-cmake](https://github.com/shinchiro/mpv-winbuild-cmake)，为 Windows 构建带外部音轨 seek 修复的 **GPL x86_64-v3 libmpv**。


## 构建与下载

- 保留上游 GPL 依赖、Clang/LTO 和打包流程。只发布 `mpv-dev-x86_64-v3-*.7z` 与 `sha256.txt`。
- 开发包包含 `libmpv-2.dll`、导入库和头文件；不发布 ffmpeg.exe、mpv 播放器或调试包。不构建 LGPL 变体。
- 成品在构建 runner 内校验 DLL 补丁标记和归档，再直接上传 Release；发布不依赖 Actions artifacts。
- Release 标签指向本仓库的工作流/补丁提交，说明中记录实际编译的 MPV 源码提交。
- 公开仓库只使用标准 GitHub-hosted runner 和仓库自带的 `GITHUB_TOKEN`，不需要个人访问令牌。

## 自动构建

`Daily Build` 每天 UTC 12:17（北京时间 20:17）执行，也可手动运行。GitHub 定时调度可能延迟。

首次运行先构建 **LLVM → toolchain（MinGW 与 Rust）→ MPV → Release**，各阶段成功后才触发下一阶段。后续每日复用缓存构建 MPV；LLVM 每隔至少 7 天更新，缓存缺失时自动选择对应的引导流程。同类工作流不会并发构建；日程遇到尚未结束的构建链会跳过本次派发。

也可以手动运行 `LLVM`，保留 `trigger_toolchain=true`、`trigger_build=true` 并设置 `release=true`。首次构建 LLVM 耗时较长；检查当前 job 的实际步骤，不要把正在构建工具链误认为 MPV 已开始编译。

- Release 按发布时间只保留最近 48 小时，日程和成功发布后都会清理；不会删除源码提交或 Git 标签。
- Actions 工件只保留 2 天。日志上传是辅助步骤，其失败不会阻止已校验 DLL 发布。
- 手动关闭 `release` 时，DLL 开发包才通过 Actions artifact 提供，仍受 artifact 配额约束。
- 更新上游时保留本仓库工作流配置与 `mpv-patches/`，不要重新引入旧依赖补丁。以当前上游修复为准。

## 音轨补丁

`mpv-patches/apply_external_audio_seek_patch.py` 按函数与唯一语义锚点修改 MPV，而不是依赖固定行号。非精确、向后关键帧 seek 时，外部音轨等待视频实际起点，再对齐音频；内部音轨、精确 seek 等路径保留上游行为。该补丁不是对所有外部/内部音轨行为的整体重写。

`install_mpv_patch_command.py` 将它挂入 CMake 的 MPV `PATCH_COMMAND`，保证在 `ninja update` 与 `mpv-fullclean` 重置源码之后执行。重复应用不会重复插入；锚点不唯一、补丁残缺或上游出现未知 patch 命令时立即失败，需要审查兼容性，不会无补丁静默发布。

每次发布会在实际 DLL 中验证补丁日志标记。此检查不能代替播放器中对音画同步的实际测试。

## Information about packages

same as [shinchiro](https://github.com/shinchiro/mpv-winbuild-cmake/blob/master/README.md#information-about-packages) [![](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fshinchiro%2Fmpv-winbuild-cmake&cacheSeconds=1800)](https://github.com/shinchiro/mpv-winbuild-cmake)

-   Git/Hg
    -   amf-headers [![amf-headers](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FGPUOpen-LibrariesAndSDKs%2FAMF&cacheSeconds=1800)](https://github.com/GPUOpen-LibrariesAndSDKs/AMF/tree/master/amf/public/include)
    -   ANGLE [![ANGLE](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fgoogle%2Fangle%2Fmain&cacheSeconds=1800)](https://github.com/google/angle)
    -   aom [![aom](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fm-ab-s%2Faom&cacheSeconds=1800)](https://aomedia.googlesource.com/aom)
    -   avisynth-headers [![avisynth-headers](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FAviSynth%2FAviSynthPlus&cacheSeconds=1800)](https://github.com/AviSynth/AviSynthPlus)
    -   bzip2 [![bzip2](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.com%2Fbzip2%2Fbzip2&cacheSeconds=1800)](https://gitlab.com/bzip2/bzip2)
    -   curl (with [c-ares](https://github.com/c-ares/c-ares), [libpsl](https://github.com/rockdaboot/libpsl), [nghttp2](https://github.com/nghttp2/nghttp2), [nghttp3](https://github.com/ngtcp2/nghttp3), [ngtcp2](https://github.com/ngtcp2/ngtcp2)) [![curl](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fcurl%2Fcurl&cacheSeconds=1800)](https://github.com/curl/curl)
    -   dav1d [![dav1d](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Fdav1d&cacheSeconds=1800)](https://code.videolan.org/videolan/dav1d/)
    -   davs2 [![davs2](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fsaindriches%2Fdavs2&cacheSeconds=1800)](https://github.com/saindriches/davs2)
    -   FFmpeg [![FFmpeg](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FFFmpeg%2FFFmpeg&cacheSeconds=1800)](https://github.com/FFmpeg/FFmpeg)
    -   fontconfig [![fontconfig](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.freedesktop.org%2Ffontconfig%2Ffontconfig&cacheSeconds=1800)](https://gitlab.freedesktop.org/fontconfig/fontconfig)
    -   freetype2 [![freetype2](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Ffreetype%2Ffreetype&cacheSeconds=1800)](https://github.com/freetype/freetype)
    -   fribidi [![fribidi](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Ffribidi%2Ffribidi&cacheSeconds=1800)](https://github.com/fribidi/fribidi)
    -   harfbuzz [![harfbuzz](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fharfbuzz%2Fharfbuzz%2Fmain&cacheSeconds=1800)](https://github.com/harfbuzz/harfbuzz)
    -   lame [![lame](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.com%2Fshinchiro%2F%2Flame&cacheSeconds=1800)](https://gitlab.com/shinchiro/lame)
    -   lcms2 [![lcms2](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fmm2%2FLittle-CMS&cacheSeconds=1800)](https://github.com/mm2/Little-CMS)
    -   libarchive [![libarchive](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Flibarchive%2Flibarchive&cacheSeconds=1800)](https://github.com/libarchive/libarchive)
    -   libaribcaption [![libaribcaption](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fxqq%2Flibaribcaption&cacheSeconds=1800)](https://github.com/xqq/libaribcaption)
    -   libass [![libass](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Flibass%2Flibass&cacheSeconds=1800)](https://github.com/libass/libass)
    -   libbluray [![libbluray](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Flibbluray&cacheSeconds=1800)](https://code.videolan.org/videolan/libbluray)
    -   libbs2b [![libbs2b](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Falexmarsev%2Flibbs2b&cacheSeconds=1800)](https://github.com/alexmarsev/libbs2b)
    -   libdvdcss [![libdvdcss](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Flibdvdcss&cacheSeconds=1800)](https://code.videolan.org/videolan/libdvdcss)
    -   libdvdnav [![libdvdnav](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Flibdvdnav&cacheSeconds=1800)](https://code.videolan.org/videolan/libdvdnav)
    -   libdvdread [![libdvdread](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Flibdvdread&cacheSeconds=1800)](https://code.videolan.org/videolan/libdvdread)
    -   libjpeg [![libjpeg](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Flibjpeg-turbo%2Flibjpeg-turbo%2Fmain&cacheSeconds=1800)](https://github.com/libjpeg-turbo/libjpeg-turbo)
    -   libjxl (with [brotli](https://github.com/google/brotli), [highway](https://github.com/google/highway)) [![libjxl](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Flibjxl%2Flibjxl%2Fmain&cacheSeconds=1800)](https://github.com/libjxl/libjxl)
    -   libmodplug [![libmodplug](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FKonstanty%2Flibmodplug&cacheSeconds=1800)](https://github.com/Konstanty/libmodplug)
    -   libmysofa [![libmysofa](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fhoene%2Flibmysofa%2Fmain&cacheSeconds=1800)](https://github.com/hoene/libmysofa)
    -   libplacebo (with [glad](https://github.com/Dav1dde/glad), [fast_float](https://github.com/fastfloat/fast_float), [xxhash](https://github.com/Cyan4973/xxHash)) [![libplacebo](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fhaasn%2Flibplacebo&cacheSeconds=1800)](https://github.com/haasn/libplacebo)
    -   libpng [![libpng](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fglennrp%2Flibpng&cacheSeconds=1800)](https://github.com/glennrp/libpng)
    -   libsdl2 [![libpng](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Flibsdl-org%2FSDL%2FSDL2&style=flat-square&cacheSeconds=1800)](https://github.com/libsdl-org/SDL)
    -   libsoxr [![libsoxr](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.com%2Fshinchiro%2Fsoxr&cacheSeconds=1800)](https://gitlab.com/shinchiro/soxr)
    -   libsrt [![libsrt](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FHaivision%2Fsrt&cacheSeconds=1800)](https://github.com/Haivision/srt)
    -   libssh [![libssh](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.com%2Flibssh%2Flibssh-mirror&cacheSeconds=1800)](https://git.libssh.org/projects/libssh.git)
    -   libudfread [![libdvdcss](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Flibudfread&cacheSeconds=1800)](https://code.videolan.org/videolan/libudfread)
    -   libunibreak [![libunibreak](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fadah1972%2Flibunibreak&cacheSeconds=1800)](https://github.com/adah1972/libunibreak)
    -   libva [![libva](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fintel%2Flibva&cacheSeconds=1800)](https://github.com/intel/libva)
    -   libvpl [![libvpl](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fintel%2Flibvpl&cacheSeconds=1800)](https://github.com/intel/libvpl)
    -   libvpx [![libvpx](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fwebmproject%2Flibvpx%2Fmain&cacheSeconds=1800)](https://chromium.googlesource.com/webm/libvpx)
    -   libwebp [![libwebp](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fwebmproject%2Flibwebp%2Fmain&cacheSeconds=1800)](https://chromium.googlesource.com/webm/libwebp)
    -   libxml2 [![libxml2](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.gnome.org%2FGNOME%2Flibxml2&cacheSeconds=1800)](https://gitlab.gnome.org/GNOME/libxml2)
    -   libzimg (with [graphengine](https://github.com/sekrit-twc/graphengine)) [![libzimg](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fsekrit-twc%2Fzimg&cacheSeconds=1800)](https://github.com/sekrit-twc/zimg)
    -   libzvbi [![libzvbi](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fzapping-vbi%2Fzvbi%2Fmain&cacheSeconds=1800)](https://github.com/zapping-vbi/zvbi)
    -   luajit [![luajit](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fopenresty%2Fluajit2%2Fv2.1-agentzh&cacheSeconds=1800)](https://github.com/openresty/luajit2)
    -   mpv [![mpv](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fmpv-player%2Fmpv&cacheSeconds=1800)](https://github.com/mpv-player/mpv)
    -   mujs [![mujs](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fcodeberg%2Fccxvii%2Fmujs&cacheSeconds=1800)](https://codeberg.org/ccxvii/mujs)
    -   nvcodec-headers [![nvcodec-headers](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FFFmpeg%2Fnv-codec-headers&cacheSeconds=1800)](https://git.videolan.org/?p=ffmpeg/nv-codec-headers.git)
    -   ogg [![ogg](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fxiph%2Fogg&cacheSeconds=1800)](https://github.com/xiph/ogg)
    -   openal-soft [![openal-soft](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fkcat%2Fopenal-soft&cacheSeconds=1800)](https://github.com/kcat/openal-soft)
    -   openssl [![openssl](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fopenssl%2Fopenssl&cacheSeconds=1800)](https://github.com/openssl/openssl)
    -   opus [![opus](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fxiph%2Fopus&cacheSeconds=1800)](https://github.com/xiph/opus)
    -   rubberband (with [libsamplerate](https://github.com/libsndfile/libsamplerate.git)) [![rubberband](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fbreakfastquay%2Frubberband%2Fdefault&cacheSeconds=1800)](https://github.com/breakfastquay/rubberband)
    -   shaderc (with [spirv-headers](https://github.com/KhronosGroup/SPIRV-Headers), [spirv-tools](https://github.com/KhronosGroup/SPIRV-Tools), [glslang](https://github.com/KhronosGroup/glslang)) [![shaderc](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fgoogle%2Fshaderc%2Fmain&cacheSeconds=1800)](https://github.com/google/shaderc)
    -   speex [![speex](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fxiph%2Fspeex&cacheSeconds=1800)](https://github.com/xiph/speex)
    -   spirv-cross [![spirv-cross](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FKhronosGroup%2FSPIRV-Cross%2Fmain&cacheSeconds=1800)](https://github.com/KhronosGroup/SPIRV-Cross)
    -   subrandr [![subrandr](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fafishhh%2Fsubrandr%2Fmaster&cacheSeconds=1800)](https://github.com/afishhh/subrandr)
    -   svtav1 [![svtav1](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.com%2FAOMediaCodec%2FSVT-AV1&cacheSeconds=1800)](https://gitlab.com/AOMediaCodec/SVT-AV1)
    -   uavs3d [![uavs3d](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fuavs3%2Fuavs3d&cacheSeconds=1800)](https://github.com/uavs3/uavs3d)
    -   uchardet [![uchardet](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fgitlab.freedesktop.org%2Fuchardet%2Fuchardet&cacheSeconds=1800)](https://gitlab.freedesktop.org/uchardet/uchardet)
    -   vorbis [![vorbis](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fxiph%2Fvorbis&cacheSeconds=1800)](https://github.com/xiph/vorbis) 
    -   vulkan [![Vulkan](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FKhronosGroup%2FVulkan-Loader%2Fmain&cacheSeconds=1800)](https://github.com/KhronosGroup/Vulkan-Loader) 
    -   vulkan-header [![Vulkan-Headers](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2FKhronosGroup%2FVulkan-Headers%2Fmain&cacheSeconds=1800)](https://github.com/KhronosGroup/Vulkan-Headers)
    -   x264 [![x264](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgitlab%2Fcode.videolan.org%2Fvideolan%2Fx264&cacheSeconds=1800)](https://code.videolan.org/videolan/x264)
    -   x265 (multilib) [![x265](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fbitbucket%2Fmulticoreware%2Fx265_git&cacheSeconds=1800)](https://bitbucket.org/multicoreware/x265_git)
    -   xz [![xz](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Ftukaani-project%2Fxz&cacheSeconds=1800)](https://github.com/tukaani-project/xz)
    -   zlib [![zlib](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Fzlib-ng%2Fzlib-ng&cacheSeconds=1800)](https://github.com/zlib-ng/zlib-ng)
    -   zstd [![zstd](https://img.shields.io/endpoint?url=https%3A%2F%2Flatest-commit-badgen.vercel.app%2Fgithub%2Ffacebook%2Fzstd%2Fdev&cacheSeconds=1800)](https://github.com/facebook/zstd)

-   Zip
    -   [lzo](https://fossies.org/linux/misc/) (2.10)
    -   [libopenmpt](https://lib.openmpt.org/libopenmpt/download/) (0.7.12)
    -   [libiconv](https://ftp.gnu.org/pub/gnu/libiconv/) (1.18)
    -   [vapoursynth](https://github.com/vapoursynth/vapoursynth)  ![](https://img.shields.io/github/v/release/vapoursynth/vapoursynth?style=flat-square&cacheSeconds=1800)




