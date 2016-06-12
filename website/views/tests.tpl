% rebase('index.tpl', active='tests')

<table class="table">
    <thead>
        <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Results</th>
            <th>Version</th>
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
                    {{test['version']}}
                </td>

                <td>
                    {{test['date']}}
                </td>
            </tr>

        %end
    </tbody>
</table>

