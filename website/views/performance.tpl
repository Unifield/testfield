% rebase('index.tpl', active='performances')

<table class="table">
    <thead>
        <tr>
            %for header in headers:
                <th>{{header}}</th>
            %end
        </tr>
    </thead>

    <tbody>
        %for row in table:
            <tr>
                %for i, cell in enumerate(row):
                    <td>
                        %if i == 0:
                            {{cell}}
                        %else:
                            {{'%.2f' % cell if cell is not None else ''}}
                        %end
                    </td>
                %end
            </tr>
        %end
    </tbody>
</table>

<img class="center-block" src="/performance/{{test}}/{{metric}}/img"/>
