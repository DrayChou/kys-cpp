// ZipFile 的占位实现：abc 的 --trans-indexka 功能需要 libzip，
// 本机 libzip 与 zlib 的 zip.h 冲突，因此这里给出空实现，仅保证链接通过。
#include "ZipFile.h"

ZipFile::ZipFile() { }
ZipFile::~ZipFile() { }
void ZipFile::openRead(const std::string&) { }
void ZipFile::openWrite(const std::string&) { }
void ZipFile::create(const std::string&) { }
void ZipFile::setPassword(const std::string&) const { }
std::string ZipFile::readFile(const std::string&) const { return std::string(); }
void ZipFile::readFileToBuffer(const std::string&, std::vector<char>&) const { }
void ZipFile::addData(const std::string&, const char*, int) { }
void ZipFile::addFile(const std::string&, const std::string&) { }
void ZipFile::removeFile(const std::string&) { }
std::vector<std::string> ZipFile::getFileNames() const { return {}; }
std::string ZipFile::u8name(const std::string& filename) { return filename; }
