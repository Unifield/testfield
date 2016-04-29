<html>
    <head>
        <title>
            Scenario: {{scenario.name}}
        </title>

        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>

    </head>

    <body>

        <div class="container">
            <h1>{{scenario.name}}</h1>

            <p>
                Tags:
                %for tag in scenario.tags:
                    <span class="label label-primary">{{tag}}</span>
                %end
            </p>

            <table class="table">
                <thead>
                    <tr>
                        <th>Steps</th>
                        <th>Printscreen</th>
                    </tr>
                </thead>

                <tbody>
                    %for printscreen in printscreens:
                        <tr>
                            <td>
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
                            </td>
                            <td>
                                <div class="text-left">
                                    <img src='{{printscreen.filename}}' width='600px'>
                                </div>
                            </td>
                        </tr>
                    %end
                </tbody>
            </table>
        </div>
    </body>
</html>

