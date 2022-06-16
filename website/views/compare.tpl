% rebase('index.tpl', active='tests')
<style>
.container {
   margin-left: 0 ! important;
   width: auto;
}
</style>
<table class="table">
    <thead>
        <tr>
            <th>Test</th>

	% for test in ordered_tests:
            <th><a href="/test/{{test}}/index.html">{{list_tests[test]['name']}}</a></th>
        % end

        </tr>
    </thead>

    <tbody>
	% for tf in all_results:
	    % if len(all_results[tf]) != len(list_tests) or len(set([x['failure'] for x in all_results[tf].values()])) > 1:
                <tr>
		    <th
		       % if dup.get(tf):
			   class="danger"
		       % end
			>{{tf}}</th>
	        % for test in ordered_tests:
		    <td 
			% if all_results[tf].get(test, {}).get('failure', '') == 'KO':
				class="danger"
			% elif all_results[tf].get(test, {}).get('failure', '') == 'OK':
				class="success"
		        % end
			>
                       <p><a href="{{all_results[tf].get(test, {}).get('link', '')}}">{{all_results[tf].get(test, {}).get('number', '')}} {{all_results[tf].get(test, {}).get('failure', '')}}</a></p>
		       <p class="small">{{all_results[tf].get(test, {}).get('filename', '')}}</p>
	            </td>
                % end

		</tr>
            % end
        % end
    </tbody>
</table>

