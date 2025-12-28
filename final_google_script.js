/**
 * MASTER JOB APPLICATION SCRIPT
 * 
 * Features:
 * 1. Saves generated questions to this Google Sheet.
 * 2. Creates Google Forms for Job Applications automatically.
 * 3. Automatically sends Form responses back to your App (Candidate Scoring).
 * 
 * NOTE: Recent advancements (AI Detection, Advanced Scoring, Rejection Emails)
 * are handled by the Python backend. This script simply delivers the data.
 * 
 * SETUP:
 * 1. Update the WEBHOOK_URL below to your Vercel App's URL.
 * 2. Deploy as Web App:
 *    - Click "Deploy" > "New deployment"
 *    - Select "Web app"
 *    - Execute as: "Me"
 *    - Who has access: "Anyone"
 *    - Click "Deploy" and copy the URL.
 */

// ================= CONFIGURATION =================
// 1. FOR PRODUCTION (Vercel):
//    Replace with your Vercel App URL: https://your-app.vercel.app/api/webhook/application
//
// 2. FOR LOCAL TESTING (Ngrok):
//    Run 'python start_with_ngrok.py' and copy the Webhook URL from the terminal.
//    Example: https://a1b2-c3d4.ngrok-free.app/api/webhook/application

var WEBHOOK_URL = "https://YOUR_VERCEL_APP_URL/api/webhook/application";
// =================================================

/**
 * MANUAL SETUP TRIGGER
 * Run this function if you are pasting this script directly into a Google Form.
 * It will link the form to the 'onFormSubmit' function.
 */
function setupTrigger() {
  // 1. Force Authorization for DriveApp (needed to make resumes public)
  // This line ensures Google asks for Drive permissions when you run this function.
  try {
    var _forceAuth = DriveApp.getRootFolder(); 
  } catch (e) {
    // Ignore error, we just want to trigger the auth scope
  }

  try {
    var form = FormApp.getActiveForm();
    ScriptApp.newTrigger('onFormSubmit')
      .forForm(form)
      .onFormSubmit()
      .create();
    Logger.log("Trigger set up successfully! You can now close this tab.");
  } catch (e) {
    Logger.log("Error: " + e.toString());
    Logger.log("If you are running this from a Spreadsheet, this error is expected. Use the Web App deployment instead.");
  }
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
    
    // REQUIRED for File Uploads: Collect email addresses
    try {
      form.setCollectEmail(true);
    } catch (e) {
      Logger.log("Could not set collect email: " + e);
    }
    
    // 2. Add Standard Fields
    if (data.standard_fields) {
      data.standard_fields.forEach(function(field) {
        var item;
        try {
          if (field.type === 'file') {
            item = form.addFileUploadItem();
          } else if (field.type === 'text') {
            item = form.addTextItem();
          } else if (field.type === 'email') {
            item = form.addTextItem();
            // Add Email Validation
            var emailValidation = FormApp.createTextValidation()
              .requireTextIsEmail()
              .build();
            item.setValidation(emailValidation);
          } else if (field.type === 'url') {
            item = form.addTextItem();
            // Add URL Validation
            var urlValidation = FormApp.createTextValidation()
              .requireTextIsUrl()
              .build();
            item.setValidation(urlValidation);
          } else if (field.type === 'phone') {
            item = form.addTextItem();
            // Add Phone Validation (Regex for digits)
            var phoneValidation = FormApp.createTextValidation()
              .requireTextMatchesPattern("[0-9()+\\- ]+")
              .setHelpText("Please enter a valid phone number.")
              .build();
            item.setValidation(phoneValidation);
          } else if (field.type === 'number') {
            item = form.addTextItem(); 
            var numberValidation = FormApp.createTextValidation()
              .requireNumber()
              .build();
            item.setValidation(numberValidation);
          } else {
            item = form.addTextItem();
          }
          
          item.setTitle(field.field);
          if (field.required) item.setRequired(true);
        } catch (err) {
          // Fallback: If File Upload fails (common restriction), use Text Item for URL
          if (field.type === 'file') {
            item = form.addTextItem();
            item.setTitle(field.field + " (Link)");
            item.setHelpText("Please paste a link to your Resume/CV (Google Drive, Dropbox, etc.)");
            if (field.required) item.setRequired(true);
          }
        }
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
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Add headers if sheet is empty
    if (sheet.getLastRow() === 0) {
      var headers = Object.keys(data);
      sheet.appendRow(headers);
    }
    
    // Prepare row data based on headers
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    var row = headers.map(function(header) {
      var val = data[header];
      // Convert objects to string
      if (typeof val === 'object') return JSON.stringify(val);
      return val || "";
    });
    
    sheet.appendRow(row);
    
    return ContentService.createTextOutput(JSON.stringify({"status": "success"}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (e) {
    // If running in a Form context, SpreadsheetApp might fail or return null
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": "Could not save to sheet: " + e.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
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
    
    // Attempt to get Form Description (Job Description)
    var jobDescription = "Job Application";
    try {
      var form = FormApp.openById(formResponse.getFormId());
      jobDescription = form.getDescription() || form.getTitle();
    } catch (err) {
      Logger.log("Could not get form description: " + err);
    }
    
    var payload = {
      "name": "Unknown Candidate",
      "email": email || "",
      "phone": "",
      "resume_url": "",
      "job_description": jobDescription,
      "answers": {}
    };

    // Intelligent Field Detection
    // We use a scoring system to identify fields even if admins rename them
    var bestMatches = {
      name: { score: 0, value: "" },
      phone: { score: 0, value: "" },
      resume: { score: 0, value: "" }
    };

    // Loop through responses
    for (var i = 0; i < itemResponses.length; i++) {
      var itemResponse = itemResponses[i];
      var item = itemResponse.getItem();
      var title = item.getTitle();
      var type = item.getType();
      var answer = itemResponse.getResponse();
      var titleLower = title.toLowerCase();
      
      // Always add to answers for context
      payload.answers[title] = answer;

      // --- 1. Detect Name ---
      var nameScore = 0;
      if (titleLower.includes("full name")) nameScore += 10;
      else if (titleLower.includes("candidate name")) nameScore += 10;
      else if (titleLower.includes("your name")) nameScore += 8;
      else if (titleLower === "name") nameScore += 5;
      else if (titleLower.includes("name")) nameScore += 2;
      
      // Negative weights for name to avoid false positives
      if (titleLower.includes("company")) nameScore -= 10;
      if (titleLower.includes("reference")) nameScore -= 10;
      if (titleLower.includes("manager")) nameScore -= 10;
      if (titleLower.includes("file")) nameScore -= 10;
      
      if (nameScore > bestMatches.name.score) {
        bestMatches.name = { score: nameScore, value: answer };
      }

      // --- 2. Detect Email (if not auto-collected) ---
      if (!payload.email && (titleLower.includes("email"))) {
        payload.email = answer;
      }

      // --- 3. Detect Phone ---
      var phoneScore = 0;
      if (titleLower.includes("phone")) phoneScore += 10;
      if (titleLower.includes("mobile")) phoneScore += 10;
      if (titleLower.includes("cell")) phoneScore += 10;
      if (titleLower.includes("contact number")) phoneScore += 8;
      
      if (phoneScore > bestMatches.phone.score) {
        bestMatches.phone = { score: phoneScore, value: answer };
      }

      // --- 4. Detect Resume ---
      var resumeScore = 0;
      if (type === FormApp.ItemType.FILE_UPLOAD) resumeScore += 20; // Strongest signal
      if (titleLower.includes("resume")) resumeScore += 10;
      if (titleLower.includes("cv")) resumeScore += 10;
      if (titleLower.includes("curriculum vitae")) resumeScore += 10;
      if (titleLower.includes("upload")) resumeScore += 5;
      if (titleLower.includes("attach")) resumeScore += 5;
      
      if (resumeScore > bestMatches.resume.score) {
        // Handle File Upload vs Text URL
        var resumeValue = "";
        if (type === FormApp.ItemType.FILE_UPLOAD && Array.isArray(answer) && answer.length > 0) {
           var fileId = answer[0];
           try {
             var file = DriveApp.getFileById(fileId);
             file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
             resumeValue = "https://drive.google.com/uc?export=download&id=" + fileId;
             Logger.log("Made file public: " + fileId);
           } catch (e) {
             Logger.log("Error sharing file: " + e);
             resumeValue = "https://drive.google.com/open?id=" + fileId; // Fallback
           }
        } else {
           resumeValue = answer;
        }
        
        bestMatches.resume = { score: resumeScore, value: resumeValue };
      }
    }

    // Assign best matches to payload
    if (bestMatches.name.score > 0) payload.name = bestMatches.name.value;
    if (bestMatches.phone.score > 0) payload.phone = bestMatches.phone.value;
    if (bestMatches.resume.score > 0) payload.resume_url = bestMatches.resume.value;

    // Send to Python Backend
    var options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    };

    var response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    Logger.log("Webhook Response: " + response.getContentText());
    
  } catch (error) {
    Logger.log("Error in onFormSubmit: " + error.toString());
  }
}
