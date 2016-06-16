#!/bin/bash

mkdir -p output/tests
mkdir -p output/benchmarks

echo "
#!/bin/bash

sudo docker pull hectord/autotestfield
sudo docker run --privileged -it -P -p 8080:8080 -v `pwd`/output:/output hectord/autotestfield \$@
" > run.sh

sudo chmod +x run.sh

