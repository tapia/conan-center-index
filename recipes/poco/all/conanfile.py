import os
from collections import namedtuple

from conans import ConanFile, tools
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.microsoft import VCVars
from conan.tools.layout import cmake_layout
from conans.errors import ConanException, ConanInvalidConfiguration

required_conan_version = ">=1.33.0"


class PocoConan(ConanFile):
    name = "poco"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://pocoproject.org"
    topics = ("conan", "poco", "building", "networking", "server", "mobile", "embedded")
    exports_sources = "CMakeLists.txt", "patches/**"
    generators = "CMakeDeps"
    settings = "os", "arch", "compiler", "build_type"
    license = "BSL-1.0"
    description = "Modern, powerful open source C++ class libraries for building network- and internet-based " \
                  "applications that run on desktop, server, mobile and embedded systems."
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_fork": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_fork": True,
    }
    no_copy_source = True

    _PocoComponent = namedtuple("_PocoComponent", ("option", "default_option", "deps", "is_lib", "external_deps"))
    _poco_component_tree = {
        "mod_poco": _PocoComponent("enable_apacheconnector", False, ("PocoUtil", "PocoNet", ), False, ("apr::apr", "apr-util::apr-util")),
        "PocoCppParser": _PocoComponent("enable_cppparser", False, ("PocoFoundation", ), False, ()),
        # "PocoCppUnit": _PocoComponent("enable_cppunit", False, ("PocoFoundation", ), False)),
        "PocoCrypto": _PocoComponent("enable_crypto", True, ("PocoFoundation", ), True, ("openssl::crypto", )),    # also external openssl
        "PocoData": _PocoComponent("enable_data", True, ("PocoFoundation", ), True, ()),
        "PocoDataMySQL": _PocoComponent("enable_data_mysql", True, ("PocoData", ), True, ()),
        "PocoDataODBC": _PocoComponent("enable_data_odbc", False, ("PocoData", ), True, ()),
        "PocoDataPostgreSQL": _PocoComponent("enable_data_postgresql", True, ("PocoData", ), True, ("libpq::libpq", )),    # also external postgresql
        "PocoDataSQLite": _PocoComponent("enable_data_sqlite", True, ("PocoData", ), True, ("sqlite3::sqlite3", )),  # also external sqlite3
        "PocoEncodings": _PocoComponent("enable_encodings", True, ("PocoFoundation", ), True, ()),
        # "PocoEncodingsCompiler": _PocoComponent("enable_encodingscompiler", False, ("PocoNet", "PocoUtil", ), False),
        "PocoFoundation": _PocoComponent(None, "PocoFoundation", (), True, ("zlib::zlib", "pcre::pcre")),
        "PocoJSON": _PocoComponent("enable_json", True, ("PocoFoundation", ), True, ()),
        "PocoJWT": _PocoComponent("enable_jwt", True, ("PocoJSON", "PocoCrypto", ), True, ()),
        "PocoMongoDB": _PocoComponent("enable_mongodb", True, ("PocoNet", ), True, ()),
        "PocoNet": _PocoComponent("enable_net", True, ("PocoFoundation", "PocoUtil"), True, ()),
        "PocoNetSSL": _PocoComponent("enable_netssl", True, ("PocoCrypto", "PocoUtil", "PocoNet", ), True, ("openssl::ssl", )),    # also external openssl
        "PocoNetSSLWin": _PocoComponent("enable_netssl_win", False, ("PocoNet", "PocoUtil", ), True, ()),
        "PocoPDF": _PocoComponent("enable_pdf", False, ("PocoXML", "PocoUtil", ), True, ()),
        "PocoPageCompiler": _PocoComponent("enable_pagecompiler", False, ("PocoNet", "PocoUtil", ), False, ()),
        "PocoFile2Page": _PocoComponent("enable_pagecompiler_file2page", False, ("PocoNet", "PocoUtil", "PocoXML", "PocoJSON", ), False, ()),
        "PocoPocoDoc": _PocoComponent("enable_pocodoc", False, ("PocoUtil", "PocoXML", "PocoCppParser", ), False, ()),
        "PocoRedis": _PocoComponent("enable_redis", True, ("PocoNet", ), True, ()),
        "PocoSevenZip": _PocoComponent("enable_sevenzip", False, ("PocoUtil", "PocoXML", ), True, ()),
        "PocoUtil": _PocoComponent("enable_util", True, ("PocoFoundation", "PocoXML", "PocoJSON", ), True, ()),
        "PocoXML": _PocoComponent("enable_xml", True, ("PocoFoundation", ), True, ("expat::expat", )),
        "PocoZip": _PocoComponent("enable_zip", True, ("PocoUtil", "PocoXML", ), True, ()),
        "PocoActiveRecord": _PocoComponent("enable_active_record", True, ("PocoFoundation", "PocoData", ), True, ()),
    }

    for comp in _poco_component_tree.values():
        if comp.option:
            options[comp.option] = [True, False]
            default_options[comp.option] = comp.default_option
    del comp

    def layout(self):
        cmake_layout(self)
        self.folders.source = ""

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.enable_fork
        else:
            del self.options.enable_netssl_win
        if tools.Version(self.version) < "1.9":
            del self.options.enable_encodings
        if tools.Version(self.version) < "1.10":
            del self.options.enable_data_mysql
            del self.options.enable_data_postgresql
            del self.options.enable_jwt
        if tools.Version(self.version) < "1.11":
            del self.options.enable_active_record

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if not self.options.enable_xml:
            util_dependencies = self._poco_component_tree["PocoUtil"].deps
            self._poco_component_tree["PocoUtil"] = self._poco_component_tree["PocoUtil"]._replace(dependencies = tuple(x for x in util_dependencies if x != "PocoXML"))
        if not self.options.enable_json:
            util_dependencies = self._poco_component_tree["PocoUtil"].deps
            self._poco_component_tree["PocoUtil"] = self._poco_component_tree["PocoUtil"]._replace(dependencies = tuple(x for x in util_dependencies if x != "PocoJSON"))

    def validate(self):
        if self.options.enable_apacheconnector:
            raise ConanInvalidConfiguration("Apache connector not supported: https://github.com/pocoproject/poco/issues/1764")
        if self.settings.compiler == "Visual Studio":
            if self.options.shared and "MT" in str(self.settings.compiler.runtime):
                raise ConanInvalidConfiguration("Cannot build shared poco libraries with MT(d) runtime")
        for compopt in self._poco_component_tree.values():
            if not compopt.option:
                continue
            if self.options.get_safe(compopt.option, False):
                for compdep in compopt.deps:
                    if not self._poco_component_tree[compdep].option:
                        continue
                    if not self.options.get_safe(self._poco_component_tree[compdep].option, False):
                        raise ConanInvalidConfiguration("option {} requires also option {}".format(compopt.option, self._poco_component_tree[compdep].option))
        if self.options.enable_data_sqlite:
            if self.options["sqlite3"].threadsafe == 0:
                raise ConanInvalidConfiguration("sqlite3 must be built with threadsafe enabled")
        if self.options.enable_netssl and self.options.get_safe("enable_netssl_win", False):
            raise ConanInvalidConfiguration("Conflicting enable_netssl[_win] settings")

    def requirements(self):
        self.requires("pcre/8.45")
        self.requires("zlib/1.2.11")
        if self.options.enable_xml:
            self.requires("expat/2.4.1")
        if self.options.enable_data_sqlite:
            self.requires("sqlite3/3.36.0")
        if self.options.enable_apacheconnector:
            self.requires("apr/1.7.0")
            self.requires("apr-util/1.6.1")
            # FIXME: missing apache2 recipe
            raise ConanInvalidConfiguration("apache2 is not (yet) available on CCI")
        if self.options.enable_netssl or \
                self.options.enable_crypto or \
                self.options.get_safe("enable_jwt", False):
            self.requires("openssl/1.1.1k")
        if self.options.enable_data_odbc and self.settings.os != "Windows":
            self.requires("odbc/2.3.9")
        if self.options.get_safe("enable_data_postgresql", False):
            self.requires("libpq/13.3")
        if self.options.get_safe("enable_data_mysql", False):
            self.requires("apr/1.7.0")
            self.requires("apr-util/1.6.1")
            self.requires("libmysqlclient/8.0.25")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_BUILD_TYPE"] = self.settings.build_type
        tc.variables["POCO_NO_AUTOMATIC_LIBS"] = True
        if tools.Version(self.version) < "1.10.1":
            tc.variables["POCO_STATIC"] = not self.options.shared
        for comp in self._poco_component_tree.values():
            if not comp.option:
                continue
            tc.variables[comp.option.upper()] = self.options.get_safe(comp.option, False)

        tc.variables["POCO_UNBUNDLED"] = True
        tc.variables["CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP"] = True

        def _abs_paths(dep_name, varname):
            return filter(lambda x: os.path.exists(x), [os.path.join(self.dependencies[dep_name].package_folder, e)
                    for e in getattr(self.dependencies[dep_name].new_cpp_info, varname)])

        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":  # MT or MTd
            tc.variables["POCO_MT"] = "ON" if "MT" in str(self.settings.compiler.runtime) else "OFF"

        if self.options.get_safe("enable_data_postgresql", False):
            tc.variables["PostgreSQL_ROOT_DIR"] = self.dependencies["libpq"].package_folder
            tc.variables["PostgreSQL_ROOT_INCLUDE_DIRS"] = ";".join(_abs_paths("libpq", "includedirs"))
            tc.variables["PostgreSQL_ROOT_LIBRARY_DIRS"] = ";".join(_abs_paths("libpq", "libdirs"))
            tc.variables["POSTGRESQL_FOUND"] = True
        if self.options.get_safe("enable_data_mysql", False):
            tc.variables["MYSQL_ROOT_DIR"] = self.dependencies["libmysqlclient"].package_folder
            tc.variables["MYSQL_ROOT_INCLUDE_DIRS"] = ";".join(_abs_paths("libmysqlclient", "includedirs"))
            tc.variables["MYSQL_INCLUDE_DIR"] = ";".join(_abs_paths("libmysqlclient", "includedirs"))
            tc.variables["MYSQL_ROOT_LIBRARY_DIRS"] = ";".join(_abs_paths("libmysqlclient", "libdirs"))
            tc.variables["APR_ROOT_DIR"] = self.dependencies["apr"].package_folder
            tc.variables["APR_ROOT_INCLUDE_DIRS"] = ";".join(_abs_paths("apr", "includedirs"))
            tc.variables["APR_ROOT_LIBRARY_DIRS"] = ";".join(_abs_paths("apr", "libdirs"))
            tc.variables["APRUTIL_ROOT_DIR"] = self.dependencies["apr-util"].package_folder
            tc.variables["APRUTIL_ROOT_INCLUDE_DIRS"] = ";".join(_abs_paths("apr-util", "includedirs"))
            tc.variables["APRUTIL_ROOT_LIBRARY_DIRS"] = ";".join(_abs_paths("apr-util", "libdirs"))
            tc.variables["MYSQL_FOUND"] = True
        # Disable fork
        if not self.options.get_safe("enable_fork", True):
            tc.variables["POCO_NO_FORK_EXEC"] = True

        if self.options.enable_netssl or self.options.enable_crypto or self.options.get_safe("enable_jwt", False):
            tc.variables["OPENSSL_FOUND"] = True
        tc.variables["CONAN_PACKAGE_VERSION"] = self.version
        tc.generate()

        ms = VCVars(self)
        ms.generate()

    def _patch_sources(self):
        with tools.chdir(self.folders.base_source):
            for patch in self.conan_data.get("patches", {}).get(self.version, []):
                tools.patch(**patch)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        # On Windows, Poco needs a message (MC) compiler.
        with tools.vcvars(self.settings) if self.settings.compiler == "Visual Studio" else tools.no_op():
            cmake.configure()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        CMake(self).install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "cmake"))
        tools.remove_files_by_mask(os.path.join(self.package_folder, "bin"), "*.pdb")

    def package_info(self):
        suffix = str(self.settings.compiler.runtime).lower()  \
                 if self.settings.compiler == "Visual Studio" and not self.options.shared \
                 else ("d" if self.settings.build_type == "Debug" else "")

        # Declare the components cpp_info
        for comp_name, (option_name, _, requires, is_lib, external_deps) in self._poco_component_tree.items():
            if not is_lib:
                continue
            if option_name and not self.options.get_safe(option_name, None):
                continue
            comp_cpp = self.cpp_info.components[comp_name]
            comp_cpp.libs = ["{}{}".format(comp_name, suffix)]
            comp_cpp.libdirs = ["lib"]
            comp_cpp.includedirs = ["include"]
            comp_cpp.requires = list(requires) + list(external_deps)

            if self.settings.os == "Linux":
                comp_cpp.system_libs.extend(["pthread", "dl", "rt"])

            if self.settings.compiler == "Visual Studio":
                comp_cpp.defines.append("POCO_NO_AUTOMATIC_LIBS")
            if not self.options.shared:
                comp_cpp.defines.append("POCO_STATIC=ON")
                if self.settings.os == "Windows":
                    comp_cpp.system_libs.extend(["ws2_32", "iphlpapi", "crypt32"])
                    if self.options.enable_data_odbc:
                        comp_cpp.system_libs.extend(["odbc32", "odbccp32"])
            comp_cpp.defines.append("POCO_UNBUNDLED")

            if self.options.enable_util:
                if not self.options.enable_json:
                    comp_cpp.defines.append("POCO_UTIL_NO_JSONCONFIGURATION")
                if not self.options.enable_xml:
                    comp_cpp.defines.append("POCO_UTIL_NO_XMLCONFIGURATION")

            comp_cpp.set_property("cmake_target_name", comp_name)

            # FIXME: Remove this in Conan 2.0
            comp_cpp.names["cmake_find_package"] = "Poco"
            comp_cpp.names["cmake_find_package_multi"] = "Poco"

        # Name for the cmake generators
        self.cpp_info.set_property("cmake_file_name", "Poco")

        # FIXME: Remove this in Conan 2.0
        self.cpp_info.names["cmake_find_package"] = "Poco"
        self.cpp_info.names["cmake_find_package_multi"] = "Poco"
