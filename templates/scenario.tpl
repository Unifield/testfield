<p>

    Tags:
    %for tag in scenario.tags:
        <span class="label label-primary">{{tag}}</span>
    %end
%if 'fails' in scenario.tags:
   <% label_color="label-danger" %>
%else:
   <% label_color="label-success" %>
%end
    Scenario: <span class="label {{label_color}}">{{idscenario}}. {{scenario.name}}</span>
    Filename : <span class="label label-info">{{filename}}</span>
</p>

<table class="table">
    <thead>
        <tr>
            <th>Instance</th>
            <th>Steps</th>
            <th>Printscreen</th>
        </tr>
    </thead>

    <tbody>
        %for printscreen in printscreens:
            <tr class="{{'danger' if printscreen.is_error() else ''}}">
                <td>
                    {{printscreen.instance_name or 'No'}}
                </td>
                <td>
                    %if printscreen.is_error():

                        <p class="text-danger">
                            {{printscreen.description}}
                        </p>

                    %else:

                        <ul>
                            %for sentence, table, step in printscreen.steps:
                                <li>
                                    {{sentence}}

                                    %if table:
                                        <table class="table table-condensed">
                                            <thead>
                                                <tr>
                                                    %for header in table[0]:
                                                        <th>{{header}}</th>
                                                    %end
                                                </tr>
                                            </thead>

                                            <tbody>
                                                %for row in table[1:]:
                                                    <tr>
                                                        %for cell in row:
                                                            <td>{{cell}}</td>
                                                        %end
                                                    </tr>
                                                %end
                                            </tbody>
                                        </table>
                                    %end

                                </li>
                            %end

                        </ul>
                    %end

                </td>
                <td>
                    <div class="text-left">
                        <a href='{{printscreen.filename}}'><img src='{{printscreen.filename}}' width='600px'></a>
                    </div>
                </td>
            </tr>
        %end
    </tbody>
</table>

