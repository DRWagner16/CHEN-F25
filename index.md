---
layout: default
---
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CH EN Fall 2025 Schedule Planner</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        /* ... your existing body, #controls-container, #group-toggles styles ... */
        
        /* Styles for Course Filter Checkboxes (adjust if you renamed #filter-checkboxes) */
        #course-filter-checkboxes {
            display: flex; flex-wrap: wrap; gap: 8px 12px;
            /* max-height: 200px; overflow-y: auto; */
            border: 1px solid #ddd; padding: 10px; background-color: #f9f9f9;
        }
        #course-filter-checkboxes > div {
            /* flex-basis: calc(33.333% - 12px); 3 columns, adjust as needed */
            box-sizing: border-box; display: flex; align-items: center; margin-bottom: 5px;
        }
        #course-filter-checkboxes input[type="checkbox"] { margin-right: 5px; }
        #course-filter-checkboxes label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }

        /* NEW: Styles for Instructor Filter Checkboxes */
        #instructor-filter-container { margin-top: 15px; }
        #instructor-filter-checkboxes {
            display: flex; flex-wrap: wrap; gap: 8px 12px;
            /* max-height: 150px; Adjust height as needed */
            /* overflow-y: auto; */
            border: 1px solid #ddd; padding: 10px; background-color: #f9f9f9;
            margin-top: 5px; /* Space below the instructor filter buttons */
        }
        #instructor-filter-checkboxes > div { /* Wrapper for each instructor checkbox */
            /* flex-basis: calc(33.333% - 12px); Aim for 3 columns, adjust as needed */
            box-sizing: border-box; display: flex; align-items: center; margin-bottom: 5px;
        }
        #instructor-filter-checkboxes input[type="checkbox"] { margin-right: 5px; }
        #instructor-filter-checkboxes label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
        hr { margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>CH EN Fall 2025 Schedule Planner B</h1>

    <div id="controls-container">
        <h2>Filter Courses</h2>
        <button id="select-all-courses-btn">Select All Courses</button> <button id="deselect-all-courses-btn">Deselect All Courses</button> <div id="group-toggles">
        </div>
        <hr> 
        <div id="course-filter-checkboxes"> </div>
        <hr>

        <div id="instructor-filter-container">
            <h3>Filter by Instructor</h3>
            <button id="select-all-instructors-btn">Select All Instructors</button>
            <button id="deselect-all-instructors-btn">Deselect All Instructors</button>
            <div id="instructor-filter-checkboxes">
            </div>
        </div>
    </div>

    <div id="schedule-chart-container">
    </div>

    <script>
// Place this inside the <script> tags, updating existing JavaScript

let allCourseEvents = [];
let allTaskNames = [];
let allInstructorNames = []; // NEW: To store unique instructor names
let masterCourseColorMap = {}; 
let isProgrammaticChange = false; // Flag to prevent event listener loops

function getInstructorsForCourse(courseName) {
    // Find the first event for this course to get its instructor list
    // (assuming instructors are consistent for all events of a given course Task)
    const event = allCourseEvents.find(ev => ev.Task === courseName);
    if (event && Array.isArray(event.Resource)) {
        return event.Resource.filter(instr => instr && instr !== "N/A"); // Return list of actual instructors
    }
    return [];
}

function getCoursesByInstructor(instructorName) {
    const courses = new Set();
    allCourseEvents.forEach(event => {
        if (Array.isArray(event.Resource) && event.Resource.includes(instructorName)) {
            courses.add(event.Task);
        }
    });
    return Array.from(courses);
}

function doesInstructorTeachOtherSelectedCourses(instructorName, excludeCourseName) {
    // Checks if 'instructorName' teaches any course that is currently selected,
    // other than 'excludeCourseName'.
    for (const taskName of allTaskNames) {
        if (taskName === excludeCourseName) continue;

        const courseCheckboxId = `cb-course-${taskName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
        const courseCheckbox = document.getElementById(courseCheckboxId);
        if (courseCheckbox && courseCheckbox.checked) { // If this other course is selected
            const instructorsOfThisCourse = getInstructorsForCourse(taskName);
            if (instructorsOfThisCourse.includes(instructorName)) {
                return true; // Yes, the instructor teaches another selected course
            }
        }
    }
    return false; // No, the instructor does not teach other selected courses
}

function isCourseTaughtByOtherSelectedInstructors(courseName, excludeInstructorName) {
    // Checks if 'courseName' is taught by any instructor (other than 'excludeInstructorName')
    // who is currently selected.
    const instructorsOfThisCourse = getInstructorsForCourse(courseName);
    for (const instrName of instructorsOfThisCourse) {
        if (instrName === excludeInstructorName) continue;

        const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
        const instrCheckbox = document.getElementById(instrCheckboxId);
        if (instrCheckbox && instrCheckbox.checked) { // If this other instructor is selected
            return true; // Yes, the course is taught by another selected instructor
        }
    }
    return false; // No, not taught by any other selected instructor
}

// --- Configuration for the chart (days, hours, y-axis, etc. - REMAINS THE SAME) ---
// ... (const daysOfWeekOrdered, hourTickStart, hourTickEnd, yAxisPlotRange, etc. as before) ...
const daysOfWeekOrdered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const hourTickStart = 7; const hourTickEnd = 19;
const yAxisPlotRange = [hourTickEnd + 0.5, hourTickStart - 0.5]; 
const yShapeMinVal = hourTickStart - 0.5; const yShapeMaxVal = hourTickEnd + 0.5;  
const ytickvals = []; const yticktext = [];
for (let hVal = hourTickStart; hVal <= hourTickEnd; hVal++) {
    ytickvals.push(hVal);
    let labelHourVal = hVal % 12 !== 0 ? hVal % 12 : 12;
    let amPmVal = hVal < 12 || hVal === 24 ? "AM" : "PM";
    if (hVal === 0) { labelHourVal = 12; amPmVal = "AM"; }
    if (hVal === 12) { labelHourVal = 12; amPmVal = "PM"; }
    yticktext.push(`${labelHourVal} ${amPmVal}`);
}

// --- setupFilters function (Update button IDs) ---
function setupFilters(courseTasks) {
    console.log("setupFilters called with tasks:", courseTasks);
    const courseCheckboxesDiv = document.getElementById('course-filter-checkboxes'); // Use new ID
    if (!courseCheckboxesDiv) { /* ... error handling ... */ return; }
    courseCheckboxesDiv.innerHTML = ''; 
    if (!courseTasks || courseTasks.length === 0) { /* ... warning ... */ return; }
    
    courseTasks.forEach(courseName => { /* ... create course checkboxes as before, using cb-${courseName} for ID ... */
        const checkboxId = `cb-course-${courseName.replace(/[^a-zA-Z0-9-_]/g, '')}`; // More robust ID
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox'; checkbox.id = checkboxId; checkbox.value = courseName;
        checkbox.checked = false; //checkbox.addEventListener('change', updateChart);
        // Inside setupFilters function:
        // Replace the simple: checkbox.addEventListener('change', updateChart);
        // With this more detailed event listener:

        checkbox.addEventListener('change', function(e) {
            if (isProgrammaticChange) return; // Prevent feedback loop if this change was code-triggered

            isProgrammaticChange = true; // Set flag for programmatic changes

            const courseNameChanged = e.target.value;
            const isNowChecked = e.target.checked;
            const instructorsForThisCourse = getInstructorsForCourse(courseNameChanged);

            if (isNowChecked) {
                // When a course is checked, ensure its instructors are also checked.
                instructorsForThisCourse.forEach(instrName => {
                    const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                    const instrCheckbox = document.getElementById(instrCheckboxId);
                    if (instrCheckbox && !instrCheckbox.checked) {
                        instrCheckbox.checked = true;
                        // Note: We are not dispatching 'change' on instrCheckbox to avoid complex loops.
                        // updateChart() at the end will read all current states.
                    }
                });
            } else {
                // When a course is UNCHECKED, uncheck its instructors ONLY IF those instructors
                // no longer teach any *other* courses that are still selected.
                instructorsForThisCourse.forEach(instrName => {
                    if (!doesInstructorTeachOtherSelectedCourses(instrName, courseNameChanged)) {
                        const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                        const instrCheckbox = document.getElementById(instrCheckboxId);
                        if (instrCheckbox && instrCheckbox.checked) {
                            instrCheckbox.checked = false;
                        }
                    }
                });
            }
            
            updateChart(); // Update the chart based on the new state of all checkboxes
            isProgrammaticChange = false; // Reset flag
        });
        const label = document.createElement('label');
        label.htmlFor = checkboxId; label.appendChild(document.createTextNode(courseName));
        const wrapper = document.createElement('div');
        wrapper.appendChild(checkbox); wrapper.appendChild(label);
        courseCheckboxesDiv.appendChild(wrapper);
        
        
    });

    // Use new button IDs
    const selectAllBtn = document.getElementById('select-all-courses-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => { 
            if (isProgrammaticChange) return;
            isProgrammaticChange = true;
            courseTasks.forEach(courseName => { 
                const cb = document.getElementById(`cb-course-${courseName.replace(/[^a-zA-Z0-9-_]/g, '')}`); 
                if(cb) cb.checked = true; 
            });
            // After selecting all courses, you might want to also select all relevant instructors
            // For simplicity now, we'll let individual selections handle cross-filter updates,
            // or the user can click "Select All Instructors".
            // A more advanced "Select All Courses" could also try to update instructor states intelligently.
            updateChart();
            isProgrammaticChange = false;
        });
    }

    const deselectAllBtn = document.getElementById('deselect-all-courses-btn');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => { 
            if (isProgrammaticChange) return;
            isProgrammaticChange = true;
            courseTasks.forEach(courseName => { 
                const cb = document.getElementById(`cb-course-${courseName.replace(/[^a-zA-Z0-9-_]/g, '')}`); 
                if(cb) cb.checked = false;
                // When deselecting all courses, we might also want to deselect all instructors
                // that ONLY teach these courses. This follows the complex logic.
                // For simplicity, "Deselect All Courses" just deselects courses for now.
                // The linked deselection logic will primarily trigger from individual unchecks.
            });
            // To be fully robust, deselecting all courses should then ensure instructors are
            // deselected if they no longer teach any selected courses.
            // This requires iterating through all instructors and calling doesInstructorTeachOtherSelectedCourses.
            // Let's simplify for now: "Deselect All" buttons are "master overrides" for their category.
            // The individual checkbox logic handles the intricate linking.
            // Re-evaluating all instructor checkboxes after deselecting all courses:
            allInstructorNames.forEach(instrName => {
                if (!doesInstructorTeachOtherSelectedCourses(instrName, null)) { // null as no specific course excluded
                    const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                    const instrCheckbox = document.getElementById(instrCheckboxId);
                    if (instrCheckbox) instrCheckbox.checked = false;
                }
            });
            updateChart();
            isProgrammaticChange = false;
        });
    }
    console.log("setupFilters finished successfully.");
}

// --- setupGroupToggles function (No changes needed in its internal logic) ---
// function setupGroupToggles(allUniqueTaskNames, definedGroups) { ... } (Keep as is)
function setupGroupToggles(allCourseTaskNamesForCheckboxes, definedGroups) {
    console.log("setupGroupToggles called with defined groups:", definedGroups);
    const groupTogglesDiv = document.getElementById('group-toggles');
    if (!groupTogglesDiv) { console.error("Element with ID 'group-toggles' not found!"); return; }
    groupTogglesDiv.innerHTML = ''; 
    if (Object.keys(definedGroups).length === 0) { console.warn("No groups defined."); return; }
    const sortedGroupNames = Object.keys(definedGroups).sort();
    sortedGroupNames.forEach(groupName => {
        const coursesInGroup = definedGroups[groupName];
        if (coursesInGroup.length === 0) return;
        const groupControlP = document.createElement('p');
        groupControlP.style.fontWeight = 'bold';
        groupControlP.textContent = `${groupName} (${coursesInGroup.length} courses): `;
        const groupButtonSelect = document.createElement('button');
        groupButtonSelect.textContent = `Select Group`;
        // Inside setupGroupToggles, for a group's "Select Group" button:
        groupButtonSelect.addEventListener('click', () => {
            isProgrammaticChange = true;
            const instructorsToAlsoCheck = new Set();

            coursesInGroup.forEach(courseNameInGroup => {
                const courseCheckbox = document.getElementById(`cb-course-${courseNameInGroup.replace(/[^a-zA-Z0-9-_]/g, '')}`);
                if (courseCheckbox && !courseCheckbox.checked) {
                    courseCheckbox.checked = true;
                }
                // Collect instructors for these courses
                const instructorsForThisCourse = getInstructorsForCourse(courseNameInGroup);
                instructorsForThisCourse.forEach(instr => instructorsToAlsoCheck.add(instr));
            });

            instructorsToAlsoCheck.forEach(instrName => {
                const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                const instrCheckbox = document.getElementById(instrCheckboxId);
                if (instrCheckbox && !instrCheckbox.checked) {
                    instrCheckbox.checked = true;
                }
            });

            isProgrammaticChange = false;
            updateChart();
        });
        const groupButtonDeselect = document.createElement('button');
        groupButtonDeselect.textContent = `Deselect Group`;
        groupButtonDeselect.addEventListener('click', () => {
            if (isProgrammaticChange) return; // Should not be strictly necessary here as it's a primary user action
                                             // but good if this function itself could be called programmatically.
                                             // Let's assume user click is the entry point.
            isProgrammaticChange = true; // Set flag: subsequent changes are programmatic

            console.log(`User deselected group: ${groupName}`);

            coursesInGroup.forEach(courseNameInGroup => {
                const courseCheckboxId = `cb-course-${courseNameInGroup.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                const courseCheckbox = document.getElementById(courseCheckboxId);
                if (courseCheckbox && courseCheckbox.checked) {
                    console.log(` Programmatically unchecking course: ${courseNameInGroup}`);
                    courseCheckbox.checked = false;
                }
                
                // Now, check the instructors of this just-deselected course
                const instructorsForThisCourse = getInstructorsForCourse(courseNameInGroup);
                instructorsForThisCourse.forEach(instrName => {
                    // Check if this instructor still teaches any OTHER course that remains selected
                    // The 'courseNameInGroup' is now effectively deselected for this check.
                    if (!doesInstructorTeachOtherSelectedCourses(instrName, null)) { 
                        // Passing null as excludeCourseName, or we can pass courseNameInGroup.
                        // doesInstructorTeachOtherSelectedCourses iterates ALL selected courses.
                        // Since courseNameInGroup's checkbox is now false, it won't be counted by the helper.
                        const instrCheckboxId = `cb-instructor-${instrName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                        const instrCheckbox = document.getElementById(instrCheckboxId);
                        if (instrCheckbox && instrCheckbox.checked) {
                            console.log(` Programmatically unchecking instructor: ${instrName} (no other selected courses found for them)`);
                            instrCheckbox.checked = false;
                        }
                    }
                });
            });

            isProgrammaticChange = false; // Reset flag
            updateChart(); // Update the chart once after all changes
        });
        
        groupControlP.appendChild(groupButtonSelect); // This was already there
        groupControlP.appendChild(groupButtonDeselect);
        groupTogglesDiv.appendChild(groupControlP);
    });
    console.log("setupGroupToggles finished successfully.");
}


// --- defineCourseGroupsFromData function (No changes needed in its internal logic) ---
// function defineCourseGroupsFromData(allEvents) { ... } (Keep as is, using event.CourseGroup)
function defineCourseGroupsFromData(allEvents) {
    console.log("defineCourseGroupsFromData called. Events received:", allEvents ? allEvents.length : 0);
    const groups = {};
    if (!allEvents) return groups;
    allEvents.forEach(event => {
        if (!event || typeof event.Task === 'undefined') return;
        const groupName = event.CourseGroup || "Uncategorized"; 
        const taskName = event.Task;
        if (!groups[groupName]) groups[groupName] = new Set();
        groups[groupName].add(taskName);
    });
    const finalGroups = {};
    Object.keys(groups).sort().forEach(groupName => {
         finalGroups[groupName] = Array.from(groups[groupName]).sort();
    });
    console.log("Defined groups:", finalGroups);
    return finalGroups;
}


// --- NEW: Function to setup instructor filter checkboxes ---
function setupInstructorFilters(instructorNames) {
    console.log("setupInstructorFilters called with instructors:", instructorNames);
    const instructorCheckboxesDiv = document.getElementById('instructor-filter-checkboxes');
    if (!instructorCheckboxesDiv) {
        console.error("Element with ID 'instructor-filter-checkboxes' not found!");
        return;
    }
    instructorCheckboxesDiv.innerHTML = '';
    if (!instructorNames || instructorNames.length === 0) {
        console.warn("setupInstructorFilters: No instructor names to create checkboxes for.");
        instructorCheckboxesDiv.innerHTML = "<p>No instructors found in data.</p>";
        return;
    }

    instructorNames.forEach(name => {
        // Sanitize instructorName for ID: replace spaces, special chars, etc.
        const instructorId = `cb-instructor-${name.replace(/[^a-zA-Z0-9-_]/g, '')}`;
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = instructorId;
        checkbox.value = name;
        checkbox.checked = false; // Default to selected
        // checkbox.addEventListener('change', updateChart);
        // Inside setupInstructorFilters function:
        // Replace the simple: checkbox.addEventListener('change', updateChart);
        // With this more detailed event listener:

        checkbox.addEventListener('change', function(e) {
            if (isProgrammaticChange) return; // Prevent feedback loop

            isProgrammaticChange = true; // Set flag

            const instructorNameChanged = e.target.value;
            const isNowChecked = e.target.checked;
            const coursesByThisInstructor = getCoursesByInstructor(instructorNameChanged);

            if (isNowChecked) {
                // When an instructor is checked, ensure their courses are also checked.
                coursesByThisInstructor.forEach(courseName => {
                    const courseCheckboxId = `cb-course-${courseName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                    const courseCheckbox = document.getElementById(courseCheckboxId);
                    if (courseCheckbox && !courseCheckbox.checked) {
                        courseCheckbox.checked = true;
                    }
                });
            } else {
                // When an instructor is UNCHECKED, uncheck their courses ONLY IF those courses
                // are not also taught by another instructor who is still selected.
                coursesByThisInstructor.forEach(courseName => {
                    if (!isCourseTaughtByOtherSelectedInstructors(courseName, instructorNameChanged)) {
                        const courseCheckboxId = `cb-course-${courseName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
                        const courseCheckbox = document.getElementById(courseCheckboxId);
                        if (courseCheckbox && courseCheckbox.checked) {
                            courseCheckbox.checked = false;
                        }
                    }
                });
            }

            updateChart(); // Update the chart based on the new state of all checkboxes
            isProgrammaticChange = false; // Reset flag
        });

        const label = document.createElement('label');
        label.htmlFor = instructorId;
        label.appendChild(document.createTextNode(name));
        
        const wrapper = document.createElement('div');
        wrapper.appendChild(checkbox);
        wrapper.appendChild(label);
        instructorCheckboxesDiv.appendChild(wrapper);
    });

    document.getElementById('select-all-instructors-btn').addEventListener('click', () => {
        instructorNames.forEach(name => {
            const instructorId = `cb-instructor-${name.replace(/[^a-zA-Z0-9-_]/g, '')}`;
            const cb = document.getElementById(instructorId);
            if(cb) cb.checked = true;
        });
        updateChart();
    });

    document.getElementById('deselect-all-instructors-btn').addEventListener('click', () => {
        instructorNames.forEach(name => {
            const instructorId = `cb-instructor-${name.replace(/[^a-zA-Z0-9-_]/g, '')}`;
            const cb = document.getElementById(instructorId);
            if(cb) cb.checked = false;
        });
        updateChart();
    });
    console.log("setupInstructorFilters finished successfully.");
}

// --- plotSchedule function (No changes needed in its internal logic for this feature) ---
// function plotSchedule(filteredEvents) { ... } (Keep as is)
function plotSchedule(filteredEvents) {
    // ... (your existing plotSchedule function - make sure it's complete here)
    console.log("plotSchedule called. Filtered events:", filteredEvents ? filteredEvents.length : 0);
    const chartDivId = 'schedule-chart-container';
    const chartContainer = document.getElementById(chartDivId);
    if (!chartContainer) { console.error("Chart container not found!"); return; }
    if (!filteredEvents) filteredEvents = [];

    const traces = [];
    if (filteredEvents.length > 0) {
      const uniqueTasksInFilter = [...new Set(filteredEvents.map(event => event.Task))];
      // masterCourseColorMap should be globally defined and populated
      // const plotlyColors = [ ... ]; // Not needed here if masterCourseColorMap is used
      // const courseColorMap = {}; // Not needed here
      // uniqueTasksInFilter.forEach((task, i) => { courseColorMap[task] = plotlyColors[i % plotlyColors.length]; }); // Not needed here
    }


    filteredEvents.forEach(event => { 
        if (event.StartHour == null || event.DurationHours == null || event.DurationHours <= 0) { return; }
        traces.push({
            type: 'bar', x: [event.Day], y: [event.DurationHours], base: [event.StartHour],
            name: event.Task,
            marker: { color: masterCourseColorMap[event.Task] || '#A9A9A9', line: { color: 'rgba(0,0,0,0.5)', width: 0.5 } },
            text: event.Task, textposition: 'inside', insidetextanchor: 'middle',
            customdata: [event.HoverInfo], hovertemplate: '%{customdata}<extra></extra>',
            width: 0.3 
        });
    });
    
    const backgroundShapes = [];
    daysOfWeekOrdered.forEach((day, index) => { 
        backgroundShapes.push({
            type: 'rect', xref: 'x', yref: 'y', x0: index - 0.5, x1: index + 0.5,
            y0: yShapeMinVal, y1: yShapeMaxVal,
            fillcolor: (index % 2 === 0) ? 'rgba(220, 220, 220, 0.2)' : 'rgba(240, 240, 240, 0.2)',
            line: { color: 'rgba(180, 180, 180, 0.4)', width: 3 }, layer: 'below'
        });
    });

    const layout = { 
        // title: 'Weekly Course Schedule',
        xaxis: { title: 'Day of the Week', categoryorder: 'array', categoryarray: daysOfWeekOrdered, side: 'top', type: 'category', tickangle: 0 },
        yaxis: { title: 'Time of Day', range: yAxisPlotRange, tickvals: ytickvals, ticktext: yticktext },
        barmode: 'group', hovermode: 'closest', bargroupgap: 2, bargap: 0.3, 
        showlegend: false, legend: { title: { text: 'Courses' } },
        margin: { t: 80, b: 50, l: 70, r: 30 }, shapes: backgroundShapes
    };
    
    try {
        Plotly.react(chartDivId, traces, layout);
        console.log(`Plotly.react called. Traces: ${traces.length}.`);
    } catch (e) { console.error("Error in Plotly.react:", e); }
}


// --- updateChart function (MODIFIED to include instructor filter) ---
// --- MODIFIED: updateChart function ---
// Place this inside the <script> tags, replacing your existing updateChart function

function updateChart() {
    console.log("updateChart called.");
    const selectedCourses = [];
    if (allTaskNames && allTaskNames.length > 0) {
        allTaskNames.forEach(taskName => {
            const checkbox = document.getElementById(`cb-course-${taskName.replace(/[^a-zA-Z0-9-_]/g, '')}`);
            if (checkbox && checkbox.checked) {
                selectedCourses.push(taskName);
            }
        });
    }
    console.log("Selected courses:", selectedCourses);

    const selectedInstructors = [];
    if (allInstructorNames && allInstructorNames.length > 0) {
        allInstructorNames.forEach(instructorName => {
            const instructorId = `cb-instructor-${instructorName.replace(/[^a-zA-Z0-9-_]/g, '')}`;
            const checkbox = document.getElementById(instructorId);
            if (checkbox && checkbox.checked) {
                selectedInstructors.push(instructorName);
            }
        });
    }
    console.log("Selected instructors:", selectedInstructors);

    const eventsToPlot = allCourseEvents.filter(event => {
        let coursePasses = true; // Default: pass this filter dimension
        // If the user has made specific selections in the course filter, apply them.
        // An empty selectedCourses list means "don't filter by course name / show all courses for this dimension".
        if (selectedCourses.length > 0) {
            coursePasses = selectedCourses.includes(event.Task);
        }
        // If selectedCourses is empty, coursePasses remains true.

        let instructorPasses = true; // Default: pass this filter dimension
        // If the user has made specific selections in the instructor filter, apply them.
        // An empty selectedInstructors list means "don't filter by instructor / show all instructors for this dimension".
        if (selectedInstructors.length > 0) {
            if (Array.isArray(event.Resource)) {
                instructorPasses = event.Resource.some(instr => selectedInstructors.includes(instr.trim()));
            } else { // Assuming event.Resource is a string if not an array
                instructorPasses = selectedInstructors.includes(String(event.Resource).trim());
            }
        }
        // If selectedInstructors is empty, instructorPasses remains true.
        
        // An event is shown if it passes both active filter dimensions.
        // If a dimension has no active selections, it effectively passes all items for that dimension.
        return coursePasses && instructorPasses;
    });
    
    console.log("Events to plot after all filters:", eventsToPlot.length);
    plotSchedule(eventsToPlot);
}

// --- MODIFIED: Initial Load (fetch.then(...) block) ---
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded. Starting script...");
    fetch('course_data.json')
        .then(response => { 
            console.log("Fetch response status:", response.status);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("Data fetched. Events:", data ? data.length : 0);
            allCourseEvents = data || [];

            if (allCourseEvents.length > 0) {
                allTaskNames = [...new Set(allCourseEvents.map(event => event.Task).filter(task => task != null))].sort();
                
                // --- Populate allInstructorNames with unique individual instructors ---
                const uniqueIndividualInstructors = new Set();
                allCourseEvents.forEach(event => {
                    if (Array.isArray(event.Resource)) {
                        event.Resource.forEach(instr => {
                            if (instr && instr.trim() !== "" && instr !== "N/A") { // Add valid, non-empty, non-"N/A" instructors
                                uniqueIndividualInstructors.add(instr.trim());
                            }
                        });
                    } else if (event.Resource && typeof event.Resource === 'string' && event.Resource.trim() !== "" && event.Resource !== "N/A") {
                        // Fallback for safety, though Python should always make it an array
                        uniqueIndividualInstructors.add(event.Resource.trim());
                    }
                });
                allInstructorNames = [...uniqueIndividualInstructors].sort();
                console.log("Unique Individual Instructors for filters:", allInstructorNames);
                // --- End instructor names population ---

                // Create Master Course Color Map (as defined in previous step)
                // ... (masterCourseColorMap logic remains the same) ...
                const preDefinedColors = [ '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5', '#393b79', '#5254a3', '#6b6ecf', '#9c9ede', '#637939', '#8ca252', '#b5cf6b', '#cedb9c', '#8c6d31', '#bd9e39', '#e7ba52', '#e7cb94', '#843c39', '#ad494a', '#d6616b', '#e7969c', '#7b4173', '#a55194', '#ce6dbd', '#de9ed6' ];
                masterCourseColorMap = {};
                allTaskNames.forEach((taskName, index) => { masterCourseColorMap[taskName] = preDefinedColors[index % preDefinedColors.length]; });


                const definedGroups = defineCourseGroupsFromData(allCourseEvents); // Uses event.CourseGroup
                
                if (allTaskNames.length > 0) setupFilters(allTaskNames);
                
                if (allInstructorNames.length > 0) setupInstructorFilters(allInstructorNames); 
                else {
                    const idf = document.getElementById('instructor-filter-checkboxes');
                    if(idf) idf.innerHTML = "<p>No instructors available to filter.</p>";
                }
                
                if (Object.keys(definedGroups).length > 0) setupGroupToggles(allTaskNames, definedGroups);
                
                updateChart();
            } else { /* ... handling for no course data ... */ }
        })
        .catch(error => { /* ... error handling ... */ });
});
    </script>
</body>
</html>
