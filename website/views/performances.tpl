% rebase('index.tpl', active='performances')

<table class="table">
    <thead>
        <tr>
            <th>Code</th>
            <th>Description</th>
            <th>Columns</th>
            %for version in versions:
                <th>{{version}}</th>
            %end
        </tr>
    </thead>
    <tbody>
        %for test, in_version in versions_by_test.iteritems():
            <tr>

                <%
                    columns = []
                %>

                    %for version in versions:
                        %if version in config_by_test_by_version and test in config_by_test_by_version[version]:
                            <%
                            columns.extend(config_by_test_by_version[version][test][0].keys())
                            %>
                        %end
                    %end
                <%
                    columns = set(columns)
                %>

                <td rowspan="{{len(columns)}}">
                    {{test}}
                </td>

                <td rowspan="{{len(columns)}}">
                    %if versions[0] in config_by_test_by_version and test in config_by_test_by_version[versions[0]]:
                        {{config_by_test_by_version[versions[0]][test][1].get('description', 'N/A')}}
                    %end
                </td>


                %for i, column in enumerate(columns):

                    <td>
                        <a href="/performance/{{test}}/{{column}}">
                            {{column}}
                        </a>
                    </td>

                    %for version in versions:
                        <td>
                            %if versions[0] in config_by_test_by_version and test in config_by_test_by_version[version] and config_by_test_by_version[version][test][0]:
                                <span class="glyphicon glyphicon-ok"></span>
                            %end
                        </td>
                    %end

                    </tr>

                    %if i != len(columns)-1:
                        <tr>
                    %end

                %end


            </tr>
        %end
    </tbody>
</table>

