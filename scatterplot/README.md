## Gradescope Autograder Assignment
### D3 Scatterplot

This assignment uses a manual Docker configuration for Gradescope.  After modifying this autograder,
the Docker image must be built & pushed to Dockerhub. 

### Steps to build & push Docker image 

Run `docker` commands in the `scatterplot/` directory (note period `.` at the  end of the command must be typed)

1. 
    `docker build -t <tag name> .`

    e.g., `docker build -t my_gs .` 


2. `docker tag <image ID> DOCKER_USERNAME/autograder-example:PROJECT_NAME`

    e.g., `docker tag 182be490832f cse6242/autograder-example:scatterplot`
    
3. `docker push DOCKER_USERNAME/autograder-example:PROJECT_NAME`

    e.g., `docker push cse6242/autograder-example:scatterplot`
    
4. In Gradescope under "Manual Docker Configuration" reference the image Docker Image Name:

    e.g., `cse6242/autograder-example:scatterplot` 
    

### easy local testing
run `./local_run_autograder`
    
### or manual local testing
1. In `scatterplot/submission/`, run `python3 -m http.server 8080 &`
2. run `run_tests.py` 
3. After testing, run `npx  kill-port 8080`

### Directory Structure Notes
- `data/` contains `cars.json` copied into `submission/` folder during grading.
- `lib/` contains all `d3` libraries that are copied into `submission/` folder during grading
- `utils/` contains `selenium` drivers for chrome and firefox for local testing
- `utils/embedded_d3.py` is a wrapper class to represent elements of the `d3` barplot.
