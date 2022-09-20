# Instructions on running script #

1. Create a folder within `analysis-uiSCL/scripts` named `edited_gtfs_files` and `removed_stops`
2. Update `PROJECT_NAME` AND `PROJECT_ID` variables in the `RemoveStops.py` file to be the name and id of your default project. You can find the project ID by clicking into the project and looking at the URL. It is the value right after "projects". For example, for the URL http://localhost:3000/regions/632627bc7d11df3df58d68bd/projects/63262801794e73312149e3f4/modifications, the project ID is 63262801794e73312149e3f4. 
3. Adjust the `FILES_TO_DO` to include the file numbers in which we still need to iterate through. 
4. Run `python RemoveStops.py`. 

## Troubleshooting ##

If Conveyal gives an error that there are too many scenarios, or if you notice that the terminal output in r5SCL throws a heap error, quit both the frontend and backend and script. Then, restart frontend and backend servers and run the script again. 

If you get an "Address already in use" error, you may need to run `lsof -t -i:<port>` for port 7070 or 3000 to see if there is a process is running and then kill it using `kill <pid>` with the appropriate pid.