% rebase('index.tpl', active='tests')

<style>
    progress::-moz-progress-bar {
        background-color: #006400 !important;
    }
    progress::-webkit-progress-value {
        background-color: #006400 !important;
    }

    progress.undef{
        background-color: #E0E0E0 !important;
    }

    progress {
        background-color: #F00;
        border: 0;
        color: #CCFFCC;
        height: 18px;

        background: #F00;

        appearance: none;
        -moz-appearance: none;
        -webkit-appearance: none;
    }
</style>


<table class="table">
    <thead>
        <tr>
            <th>Name</th>
            <th>Description</th>

            <th>Results</th>

            <th>Health</th>
            <th>Date</th>
        </tr>
    </thead>

    <tbody>

        %for test in tests:

            <tr class="

                %if test['result'] != 'ok':
                    danger
                %end
                ">
                <td>
                    <a href="/test/{{test['id']}}/index.html">
                        {{test['name']}}
                    </a>
                </td>
                <td>
                    <a href="/test/{{test['id']}}/index.html">
                        {{test['description']}}
                    </a>
                </td>
                <td>
                    %if test['result'] == 'ok':
                        <span class="glyphicon glyphicon-ok"></span>
                    %else:
                        <span class="glyphicon glyphicon-remove"></span>
                    %end
                </td>

                <td>
                    %if test['scenario_passed'] and test['scenario_ran']:
                        <progress value="{{test['scenario_passed']}}" max="{{test['scenario_ran']}}"></progress>
                    %else:
                        <progress class="undef" value="0" max="100"></progress>
                    %end
                </td>

                <td>
                    {{test['version']}}
                </td>

                <td>
                    {{test['date']}}
                </td>
            </tr>

        %end
    </tbody>
</table>

