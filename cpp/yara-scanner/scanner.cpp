#include "scanner.h"
#include <yara.h>

int scan_file(const char* file_path) {
    YR_COMPILER* compiler = nullptr;
    YR_RULES* rules = nullptr;
    int result = 0;

    if (yr_initialize() != ERROR_SUCCESS) return -1;
    if (yr_compiler_create(&compiler) != ERROR_SUCCESS) {
        yr_finalize();
        return -1;
    }
    
    // Временное пустое правило (замените на свои правила)
    const char* rule_text = "rule dummy { condition: true }";
    if (yr_compiler_add_string(compiler, rule_text, nullptr) != ERROR_SUCCESS) {
        yr_compiler_destroy(compiler);
        yr_finalize();
        return -1;
    }
    
    if (yr_compiler_get_rules(compiler, &rules) != ERROR_SUCCESS) {
        yr_compiler_destroy(compiler);
        yr_finalize();
        return -1;
    }
    yr_compiler_destroy(compiler);
    
    int scan_result = yr_rules_scan_file(rules, file_path, 0, nullptr, nullptr, 0);
    if (scan_result == ERROR_SUCCESS) result = 0;
    else if (scan_result == ERROR_RULES_MATCH) result = 1;
    else result = -1;
    
    yr_rules_destroy(rules);
    yr_finalize();
    return result;
}