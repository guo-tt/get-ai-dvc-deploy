REPO := porter.azurecr.io/porter/getai:0.1.0

build:
	docker build -t $(REPO) -f docker/Dockerfile .
run:
	docker run -it --rm \
	    -p 8888:8888 \
	    -v `pwd`:/srv \
	    $(REPO) 
