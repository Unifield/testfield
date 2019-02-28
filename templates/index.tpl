%for tag in alltags:
    <span data-classon="label label-primary" data-classoff="label label-default" class="label label-default">{{tag}}</span>
%end
    <span data-classon="label label-primary" data-classoff="label label-default" class="label label-default" style="color:red">danger</span>

<script>
    $(document).ready(function(){

        $("span.label").on('click', function(){
            var classon = $(this).data('classon');
            var classoff = $(this).data('classoff');

            if($(this).attr('class') == classon){
                $(this).attr('class', classoff);
            }else{
                $(this).attr('class', classon);
            }

            var elements = [];

            $("span.label").each(function(i, elem){
                if($(elem).data('classon') == $(elem).attr('class')){
                    elements.push($(elem).text());
                }
            });

            $("table tr.line").each(function(i, elem){
                values = $(elem).data("tags");
                subvalues = values.split(' ');

                ret = subvalues.filter(function(n) {
                    return elements.indexOf(n) != -1;
                });

                if(ret.length == elements.length){
                    $(elem).show();
                }else{
                    $(elem).hide();
                }
            });
        });
    });
</script>

<table class="table">
    <thead>
        <tr>
            <th>Type</th>
            <th>Scenario</th>
            <th>Percentage</th>
            <th>Time [h:m:s]</th>
            <th>Result</th>
        </tr>
    </thead>

    <tbody>
        %for valid, scenario, ratio, time, url, tags in scenarios:
            <tr data-tags="{{' '.join(tags)}}{{' danger' if not valid else ''}}" class="line {{'danger' if not valid else ''}}">

                <td>
                    <div class="text-center">

                        %if 'fails' in tags:
                            <span class="label label-danger">FAILURE</span>
                        %end

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

                <td>{{ '%.2f' % (ratio) }}</td>

		<td>{{  ('%s' % datetime.timedelta(seconds=time)).split('.')[0] if time else '' }}</td>

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

    <tfoot>
        <tr>
            <th>
                <div class="text-left">
                    {{ total_scenarios }}
                </div>
            </th>
            <th>-</th>
            <th>
                <div class="text-left">
                    {{ '%.2f' % total_percentage }}
                </div>
            </th>
            <th>
                <div class="text-left">
		    {{  ('%s' % datetime.timedelta(seconds=total_time)).split('.')[0]  }}
                </div>
            </th>
            <th>
                <div class="text-left">
                    {{ total_passed }}
                </div>
            </th>
        </tr>
    </tfoot>
</table>

