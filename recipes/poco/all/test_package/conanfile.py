import os
from conans import ConanFile, tools
from conan.tools.cmake import CMakeToolchain, CMake
from conan.tools.layout import cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)
        self.folders.source = ""

    @property
    def _with_netssl(self):
        return (
            ("enable_netssl" in self.options["poco"] and self.options["poco"].enable_netssl) or
            ("enable_netssl_win" in self.options["poco"] and self.options["poco"].enable_netssl_win)
        )

    @property
    def _with_encodings(self):
        return "enable_encodings" in self.options["poco"] and self.options["poco"].enable_encodings

    @property
    def _with_jwt(self):
        return "enable_jwt" in self.options["poco"] and self.options["poco"].enable_jwt

    def generate(self):
        toolchain = CMakeToolchain(self)
        toolchain.variables["TEST_CRYPTO"] = self.options["poco"].enable_crypto
        toolchain.variables["TEST_UTIL"] = self.options["poco"].enable_util
        toolchain.variables["TEST_NET"] = self.options["poco"].enable_net
        toolchain.variables["TEST_NETSSL"] = self._with_netssl
        toolchain.variables["TEST_SQLITE"] = self.options["poco"].enable_data_sqlite
        toolchain.variables["TEST_ENCODINGS"] = self._with_encodings
        toolchain.variables["TEST_JWT"] = self._with_jwt
        toolchain.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self.settings, skip_x64_x86=True):
            self.run(os.path.join(self.build_folder, "core"), run_environment=True)
            if self.options["poco"].enable_util:
                self.run(os.path.join(self.build_folder, "util"), run_environment=True)
            if self.options["poco"].enable_crypto:
                self.run("{} {}".format(os.path.join(self.build_folder, "crypto"), os.path.join(self.source_folder, "conanfile.py")), run_environment=True)
            if self.options["poco"].enable_net:
                self.run(os.path.join(self.build_folder, "net"), run_environment=True)
                self.run(os.path.join(self.build_folder, "net_2"), run_environment=True)
            if self._with_netssl:
                self.run(os.path.join(self.build_folder, "netssl"), run_environment=True)
            if self.options["poco"].enable_data_sqlite:
                self.run(os.path.join(self.build_folder, "sqlite"), run_environment=True)
            if self._with_encodings:
                self.run(os.path.join(self.build_folder, "encodings"), run_environment=True)
            if self._with_jwt:
                self.run(os.path.join(self.build_folder, "jwt"), run_environment=True)
