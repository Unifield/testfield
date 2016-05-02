<!DOCTYPE HTML>
<html>

    <head>
        <title>UniField</title>

        <link rel="stylesheet" href="/static/css/bootstrap.min.css">
        <script src="/static/js/bootstrap.min.js"></script>

    </head>

    <body>

        <nav class="navbar navbar-default">
            <div class="container-fluid">
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                    <a class="navbar-brand" href="#">UniField</a>
                </div>

                <!-- Collect the nav links, forms, and other content for toggling -->
                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <ul class="nav navbar-nav">

                        <li class="
                            %if active == 'tests':
                                active
                            %end
                        "><a href="/tests">Tests</a></li>


                        <li class="
                            %if active == 'performances':
                                active
                            %end
                        "><a href="/performances">Performances</a></li>

                    </ul>
                </div><!-- /.navbar-collapse -->
            </div><!-- /.container-fluid -->
        </nav>

        <div class="container">
            {{!base}}
        </div>
    </body>

</html>

