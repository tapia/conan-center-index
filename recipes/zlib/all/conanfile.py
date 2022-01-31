from conan import ConanFile
from conan.tools import Version
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import get, patch, rename, chdir, load, save
from conans.tools import replace_in_file
import os


required_conan_version = ">=1.43.0"


class ZlibConan(ConanFile):
    name = "zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://zlib.net"
    license = "Zlib"
    description = ("A Massively Spiffy Yet Delicately Unobtrusive Compression Library "
                   "(Also Free, Not to Mention Unencumbered by Patents)")
    topics = ("zlib", "compression")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    generators = "CMakeToolchain"

    def layout(self):
        cmake_layout(self)
        # self.folders.source = "source_subfolder"

    def export_sources(self):
        for _patch in self.conan_data.get("patches", {}).get(str(self.version), []):
            self.copy(_patch["patch_file"])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        try:  # FIXME: This was not failing at 1.X
            del self.settings.compiler.libcxx
            del self.settings.compiler.cppstd
        except Exception:
            pass

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], destination=self.source_folder, strip_root=True)

    def _patch_sources(self):
        for _patch in self.conan_data.get("patches", {}).get(str(self.version), []):
            # !!!! This is not easy to understand, the patches are un the base source folder, not an easy access. Here the current dir is source_folder.
            patch(self, patch_file=os.path.join(self.folders.base_source, _patch["patch_file"]))

        # https://github.com/madler/zlib/issues/268
        replace_in_file(os.path.join(self.source_folder, 'gzguts.h'), '#if defined(_WIN32) || defined(__CYGWIN__)', '#if defined(_WIN32) || defined(__MINGW32__)')

        is_apple_clang12 = self.settings.compiler == "apple-clang" and Version(str(self.settings.compiler.version)) >= "12.0"
        if not is_apple_clang12:
            for filename in ['zconf.h', 'zconf.h.cmakein', 'zconf.h.in']:
                filename = os.path.join(self.source_folder, filename)
                replace_in_file(filename,
                                      '#ifdef HAVE_UNISTD_H    '
                                      '/* may be set to #if 1 by ./configure */',
                                      '#if defined(HAVE_UNISTD_H) && (1-HAVE_UNISTD_H-1 != 0)')
                replace_in_file(filename,
                                      '#ifdef HAVE_STDARG_H    '
                                      '/* may be set to #if 1 by ./configure */',
                                      '#if defined(HAVE_STDARG_H) && (1-HAVE_STDARG_H-1 != 0)')

    def build(self):
        self._patch_sources()
        make_target = "zlib" if self.options.shared else "zlibstatic"
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target=make_target)

    def _rename_libraries(self):
        if self.settings.os == "Windows":
            lib_path = os.path.join(self.package_folder, "lib")
            suffix = "d" if self.settings.build_type == "Debug" else ""

            if self.options.shared:
                if self.settings.compiler == "Visual Studio" and suffix:
                    current_lib = os.path.join(lib_path, "zlib%s.lib" % suffix)
                    rename(self, current_lib, os.path.join(lib_path, "zlib.lib"))
            else:
                if self.settings.compiler == "Visual Studio":
                    current_lib = os.path.join(lib_path, "zlibstatic%s.lib" % suffix)
                    rename(self, current_lib, os.path.join(lib_path, "zlib.lib"))
                elif self.settings.compiler in ("clang", "gcc", ):
                    if not self.settings.os.subsystem:
                        current_lib = os.path.join(lib_path, "libzlibstatic.a")
                        rename(self, current_lib, os.path.join(lib_path, "libzlib.a"))

    def _extract_license(self):
        with chdir(self, os.path.join(self.source_folder)):
            tmp = load(self, "zlib.h")
            license_contents = tmp[2:tmp.find("*/", 1)]
            save(self, "LICENSE", license_contents)

    def package(self):
        self._extract_license()
        self.copy("LICENSE", src=self.source_folder, dst="licenses")

        # Copy headers
        for header in ["*zlib.h", "*zconf.h"]:
            self.copy(pattern=header, dst="include", src=self.source_folder, keep_path=False)
            self.copy(pattern=header, dst="include", src=self.build_folder, keep_path=False)

        # Copying static and dynamic libs
        if self.options.shared:
            self.copy(pattern="*.dylib*", dst="lib", src=self.build_folder, keep_path=False, symlinks=True)
            self.copy(pattern="*.so*", dst="lib", src=self.build_folder, keep_path=False, symlinks=True)
            self.copy(pattern="*.dll", dst="bin", src=self.build_folder, keep_path=False)
            self.copy(pattern="*.dll.a", dst="lib", src=self.build_folder, keep_path=False)
        else:
            self.copy(pattern="*.a", dst="lib", src=self.build_folder, keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src=self.build_folder, keep_path=False)

        self._rename_libraries()

    def package_info(self):
        self.cpp_info.builddirs = []
        self.cpp_info.set_property("cmake_file_name", "ZLIB")
        self.cpp_info.set_property("cmake_target_name", "ZLIB::ZLIB")
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.libs.append("zlib" if self.settings.os == "Windows" and not self.settings.os.subsystem else "z")

        # !!! .names has to be mocked
        # self.cpp_info.names["cmake_find_package"] = "ZLIB"
        # self.cpp_info.names["cmake_find_package_multi"] = "ZLIB"
