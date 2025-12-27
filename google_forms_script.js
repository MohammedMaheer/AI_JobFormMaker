/**
 * MASTER JOB APPLICATION SCRIPT
 * 
 * Features:
 * 1. Saves generated questions to this Google Sheet.
 * 2. Creates Google Forms for Job Applications automatically.
 * 3. Automatically sends Form responses back to your App (Candidate Scoring).
 * 
 * SETUP:
 * 1. Update the WEBHOOK_URL below to your App's URL (e.g. Ngrok or Render).
 * 2. Deploy as Web App:
 *    - Click "Deploy" > "New deployment"
 *    - Select "Web app"
 *    - Execute as: "Me"
 *    - Who has access: "Anyone"
 *    - Click "Deploy" and copy the URL.
 */

// ================= CONFIGURATION =================
// Replace with your Python App's URL (Ngrok or Render)
// Ensure it ends with /api/webhook/application
var WEBHOOK_URL = "https://patriarchical-conrad-overconservatively.ngrok-free.dev/api/webhook/application";
// =================================================

/**
 * RUN THIS FUNCTION ONCE TO SETUP THE TRIGGER
 */
function setupTrigger() {
  var form = FormApp.getActiveForm();
  ScriptApp.newTrigger('onFormSubmit')
    .forForm(form)
    .onFormSubmit()
    .create();
  Logger.log("Trigger set up successfully!");
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    
    // Check action type
    if (data.action === 'create_application_form') {
      return createForm(data);
    } else {
      return saveToSheet(data);
    }
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function createForm(data) {
  try {
    // 1. Create the Form
    var form = FormApp.create(data.form_title);
    form.setDescription('Job Application for ' + data.job_title + (data.company_name ? ' at ' + data.company_name : ''));
    
    // 2. Add Standard Fields
    if (data.standard_fields) {
      data.standard_fields.forEach(function(field) {
        var item;
        if (field.type === 'text' || field.type === 'email' || field.type === 'url' || field.type === 'phone') {
          item = form.addTextItem();
        } else if (field.type === 'number') {
          item = form.addTextItem(); // FormApp doesn't have specific number item, use text validation if needed
        } else {
          item = form.addTextItem();
        }
        
        item.setTitle(field.field);
        if (field.required) item.setRequired(true);
      });
    }
    
    // 3. Add Interview Questions
    form.addPageBreakItem().setTitle('Interview Questions');
    
    if (data.interview_questions) {
      data.interview_questions.forEach(function(q) {
        form.addParagraphTextItem()
          .setTitle(q.question)
          .setHelpText('Category: ' + q.category)
          .setRequired(true);
      });
    }
    
    // 4. Set up the Trigger for Automation
    // This links the new form to the 'onFormSubmit' function in THIS script
    ScriptApp.newTrigger('onFormSubmit')
      .forForm(form)
      .onFormSubmit()
      .create();
      
    // 5. Return the URLs
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "formUrl": form.getPublishedUrl(),
      "editUrl": form.getEditUrl(),
      "message": "Form created and automation trigger linked!"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (e) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": e.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function saveToSheet(data) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // Add headers if sheet is empty
  if (sheet.getLastRow() === 0) {
    var headers = Object.keys(data);
    sheet.appendRow(headers);
  }
  
  // Prepare row data
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = headers.map(function(header) {
    var val = data[header];
    if (typeof val === 'object') return JSON.stringify(val);
    return val || "";
  });
  
  sheet.appendRow(row);
  
  return ContentService.createTextOutput(JSON.stringify({"status": "success"}))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Triggered when a candidate submits the form.
 * Sends data to your Python Backend.
 */
function onFormSubmit(e) {
  try {
    var formResponse = e.response;
    var itemResponses = formResponse.getItemResponses();
    var email = formResponse.getRespondentEmail();
    
    var payload = {
      "name": "Unknown Candidate",
      "email": email || "",
      "resume_url": "",
      "job_description": "Job Application", // You might want to store the JD in the form description or properties
      "answers": {}
    };

    // Loop through responses
    for (var i = 0; i < itemResponses.length; i++) {
      var itemResponse = itemResponses[i];
      var item = itemResponse.getItem();
      var title = item.getTitle();
      var type = item.getType();
      var answer = itemResponse.getResponse();
      var titleLower = title.toLowerCase();
      
      if (titleLower.includes("name") && !titleLower.includes("company")) {
        payload.name = answer;
      } 
      else if (titleLower.includes("email") && !payload.email) {
        payload.email = answer;
      }
      // Robust Resume Detection: Check for File Upload Type OR Keywords
      else if (type === FormApp.ItemType.FILE_UPLOAD || titleLower.includes("resume") || titleLower.includes("cv") || titleLower.includes("upload")) {
        if (Array.isArray(answer) && answer.length > 0) {
          // It's a file upload (returns array of IDs)
          var fileId = answer[0];
          
          // Make the file publicly accessible so the Python app can download it
          try {
            var file = DriveApp.getFileById(fileId);
            file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
            Logger.log("Made file public: " + fileId);
          } catch (shareError) {
            Logger.log("Could not set file permissions: " + shareError.toString());
          }
          
          payload.resume_url = "https://drive.google.com/uc?export=download&id=" + fileId;
        } else {
          // It might be a text field with a URL
          payload.resume_url = answer;
        }
      }
      else {
        payload.answers[title] = answer;
      }
    }

    // Send to Python Backend
    var options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    };

    UrlFetchApp.fetch(WEBHOOK_URL, options);
    
  } catch (error) {
    Logger.log("Error in onFormSubmit: " + error.toString());
  }
}
