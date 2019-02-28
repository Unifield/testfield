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
            <th>Version</th>
            <th>Count</th>
            <th>Date</th>
            <th>Time [h:m:s]</th>
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
                    %if test['valid']:
                        <a href="/test/{{test['id']}}/index.html">
                    %end

                    {{test['name']}}

                    %if test['valid']:
                        </a>
                    %end
                </td>
                <td>
                    %if test['valid']:
                        <a href="/test/{{test['id']}}/index.html">
                    %end
                        {{test['description']}}
                    %if test['valid']:
                        </a>
                    %end
                </td>
                <td>
                    %if test['result'] == 'ok':
                        <span class="glyphicon glyphicon-ok"></span>
                    %else:
                        <span class="glyphicon glyphicon-remove"></span>
                    %end
                </td>

                <td>
                    <div style="margin-bottom: 0px; width: 100px" class="progress" data-total="{{test['scenario_ran']}}" data-passed="{{test['scenario_passed']}}">
                        <div class="progress-bar progress-bar-success" style="width: 100%">
                            <span class="progress-text-success"></span>
                        </div>
                        <div class="progress-bar progress-bar-danger" style="width: 0%">
                            <span class="progress-text-failure"></span>
                        </div>
                    </div>
                </td>

                <td>
                    {{test['version']}}
                </td>

                <td>
                    %if test['scenario_passed'] and test['scenario_ran']:
                        {{test['scenario_passed']}} / {{test['scenario_ran']}}
                    %end
                </td>

                <td>
                    {{test['date']}}
                </td>
		<td>
                    {{ ('%s' % datetime.timedelta(seconds=float(test['exec_time']))).split('.')[0] if test.get('exec_time') else '' }}
		</td>
            </tr>

        %end
    </tbody>
</table>

%if len(pages) > 1:
    <div class="row">
        <div class="col-xs-12">
            <div class="text-center">
                <nav>
                    <ul class="pagination">
                        %for is_current, nopage in pages:
                            %if not is_current:
                                <li>
                                    <a href="?page={{nopage}}">
                                        {{nopage}}
                                    </a>
                                </li>
                            %else:
                                <li class="disabled">
                                    <a href="#">
                                        {{nopage}}
                                    </a>
                                </li>

                            %end
                        %end
                    </ul>
                </nav>
            </div>
        </div>
    </div>
%end

<script language="javascript">
    $(document).ready(function(){
        $(".progress").each(function(i, pgNode){
            var node = $(pgNode);

            var total = parseFloat($(node).data("total"));
            var passed = parseFloat($(node).data("passed"));

            if(!isNaN(total) && !isNaN(passed)){

                var percentage_0_1 = passed / total;
                percentage_passed = parseInt(percentage_0_1 * 100, 10);
                percentage_failed = 100 - percentage_passed;

                node.find(".progress-bar-success").css({
                    width: percentage_passed + "%",
                })
                node.find(".progress-bar-danger").css({
                    width: percentage_failed + "%",
                })

                if(percentage_passed >= 50){
                    percentage = (Math.round(percentage_0_1 * 10000) / 100).toFixed(2);
                    class_attr = ".progress-text-success"
                }else{
                    percentage = (Math.round((1.0 - percentage_0_1) * 10000) / 100).toFixed(2);
                    class_attr = ".progress-text-failure"
                }
                node.find(class_attr).text(percentage + "%");
            }else{
                node.remove();
            }
        });
    });
</script>

