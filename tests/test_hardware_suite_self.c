#include "../examples/hardware_test_suite/self_tests.h"

int main(void)
{
    return hardware_run_pure_self_tests() == 0 ? 0 : 1;
}
