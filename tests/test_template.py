from runtests import run_preprocessor


def test_of_template_creating():
    """
    Checks whether template is processed correctly - compares generated file against the one we expect
    """
    lines = run_preprocessor("tests/test_files/Accruals_function_with_template.meta_feature")
    content = list(lines)
    with open('tests/test_files/outresult', 'w') as f:
        # remove invalid characters due to bad unifield encodings in test instances
        out = []
        for a in list(content):
            if ord(a) in range(128):
                out.append(a)
        f.write(''.join(out))

    with open('tests/test_files/Accruals_function.meta_feature', 'r') as f:
        ex_result_lines = f.readlines()

    with open('tests/test_files/outresult', 'r') as f:
        out_result_lines = f.readlines()

    assert(out_result_lines == ex_result_lines)

