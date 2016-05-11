#!/bin/bash

mkdir -p output/tests
mkdir -p output/benchmarks

echo "
#!/bin/bash

sudo docker pull hectord/testfield
sudo docker run --privileged -it -p 8080:8080 -v `pwd`/output:/output hectord/testfield \$@
" > run.sh

sudo chmod +x run.sh

