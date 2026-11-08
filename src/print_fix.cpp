// MinGW(MSYS2) 的 libstdc++ 没有实现 <print> 需要的两个终端辅助函数，
// 导致 std::print/std::println 链接期报 undefined reference。
// 这里按 bits/print.h 的声明给出等价实现：直接写 stdout。
#include <cstdio>
#include <span>
#include <system_error>

namespace std
{
    void* __open_terminal(FILE* stream)
    {
        return stream;
    }

    error_code __write_to_terminal(void* term, span<char> text)
    {
        if (term == nullptr)
        {
            return make_error_code(errc::bad_file_descriptor);
        }
        FILE* f = static_cast<FILE*>(term);
        if (text.size() > 0)
        {
            fwrite(text.data(), 1, text.size(), f);
        }
        fflush(f);
        return {};
    }
}
