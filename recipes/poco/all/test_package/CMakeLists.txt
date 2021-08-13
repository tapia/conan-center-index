cmake_minimum_required(VERSION 3.1)
project(MyHello)

set(CMAKE_CXX_STANDARD 11)

find_package(Poco REQUIRED)

add_executable(core test_core.cpp)
target_link_libraries(core Poco::Poco)

option(TEST_NET "Test Net")
if(TEST_NET)
    add_executable(net test_net.cpp)
    target_link_libraries(net Poco::PocoNet)

    add_executable(net_2 test_net_2.cpp)
    target_link_libraries(net_2 Poco::PocoNet)
endif()

option(TEST_NETSSL "Test NetSSL")
if(TEST_NETSSL)
    add_executable(netssl test_netssl.cpp)
    target_link_libraries(netssl Poco::PocoNetSSL)
endif()

option(TEST_CRYPTO "Test crypto")
if(TEST_CRYPTO)
    add_executable(tcrypto test_crypto.cpp)
    target_link_libraries(tcrypto Poco::PocoCrypto)
    set_property(TARGET tcrypto PROPERTY OUTPUT_NAME "crypto")
endif()

option(TEST_UTIL "Test Util")
if(TEST_UTIL)
    add_executable(util test_util.cpp)
    target_link_libraries(util Poco::PocoUtil)
    if(MINGW)
        target_link_options(util PRIVATE -municode)
    endif()
endif()

option(TEST_SQLITE "Test Sqlite")
if(TEST_SQLITE)
    add_executable(sqlite test_sqlite.cpp)
    target_link_libraries(sqlite Poco::PocoDataSQLite)
endif()

option(TEST_ENCODINGS "Test Encodings")
if(TEST_ENCODINGS)
    add_executable(encodings test_encodings.cpp)
    target_link_libraries(encodings Poco::PocoEncodings)
endif()

option(TEST_JWT "Test JWT")
if(TEST_JWT)
    add_executable(jwt test_jwt.cpp)
    target_link_libraries(jwt Poco::PocoJWT)
endif()
