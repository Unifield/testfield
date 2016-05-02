<table class="table">
    <thead>
        <tr>
            <th>Type</th>
            <th>Scenario</th>
            <th>Percentage</th>
            <th>Time [s]</th>
            <th>Result</th>
        </tr>
    </thead>

    <tbody>
        %for valid, scenario, ratio, time, url, tags in scenarios:
            <tr class="{{'danger' if not valid else ''}}">

                <td>
                    <div class="text-center">

                        %if 'it' in tags:
                            <span class="label label-primary">IT</span>
                        %end

                        %if 'supply' in tags:
                            <span class="label label-success">Supply</span>
                        %end

                        %if 'finance' in tags:
                            <span class="label label-warning">Finance</span>
                        %end

                        %if 'testperf' in tags:
                            <span class="label label-info">Perf</span>
                        %end

                    </div>
                </td>

                <td>
                    <a href="{{ url }}">
                        {{ scenario }}
                    </a>
                </td>

                <td>{{ ratio }}</td>

                <td>{{ time }}</td>

                <td>
                    <div class="text-center">
                        %if valid:
                            <span class="glyphicon glyphicon-ok"></span>
                        %else:
                            <span class="glyphicon glyphicon-remove"></span>
                        %end
                    </div>
                </td>

            </tr>
        %end
    </tbody>
</table>

