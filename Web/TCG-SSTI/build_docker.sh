CAT=$(basename "$(dirname "$PWD")" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
CHALL=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
NAME="${CAT}_${CHALL}"
PORT=8080
HOST_PORT=8002

docker rm -f $NAME
docker image prune -f
docker build --tag=$NAME .

RUN=false
PRIV=false

while getopts "pr" option; do
    case "$option" in
        r) RUN=true ;;
        p) PRIV=true ;;
        *) echo "Usage: $0 [-r] [-p]"; exit 1 ;;
    esac
done

if [ $RUN = true ] ; then
    if [ $PRIV = true ] ; then
        echo "RUN PRIV"
        docker run -d --privileged -p $HOST_PORT:$PORT --rm --name=$NAME $NAME
    else
        echo "RUN"
        docker run -d -p $HOST_PORT:$PORT --rm --name=$NAME $NAME
    fi
else
    echo "NO RUN"
fi