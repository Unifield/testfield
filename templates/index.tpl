<!DOCTYPE HTML>
<html>

    <head>
        <title>Results - 12.04.2015</title>

        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>

    </head>

    <body>
        <div class="container">
            <h1>UniField - Functional tests</h1>

            <p>
                This test was launched the {{date}}.
            </p>

            <table class="table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Result</th>
                        <th>Scenario</th>
                        <th>Percentage</th>
                        <th>Time [s]</th>
                    </tr>
                </thead>

                <tbody>
                    %for valid, scenario, ratio, time, url, tags in scenarios:
                        <tr>

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

                                </div>
                            </td>

                            <td>
                                <div class="text-center">
                                    %if valid:
                                        <img width="20px" src="res/success.png"/>
                                    %else:
                                        <img width="20px" src="res/failure.png"/>
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

                        </tr>
                    %end
                </tbody>
            </table>
        </div>
    </body>

</html>

