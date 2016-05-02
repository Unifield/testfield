% rebase('index.tpl', active='tests')

%if error:
    <div class="alert alert-danger">
        {{error}}
    </div>
%end

%if fichier:
    {{!fichier}}
%end


