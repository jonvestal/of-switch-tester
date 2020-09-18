lint() {
    flake8 client/ ryu/
}


case "$1" in
    lint)
       lint
       ;;
    *)
       echo "Usage: $0 {test|lint}"
esac

exit 0