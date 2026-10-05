# Restart and names update

Extract to a new folder and run START.bat. Paste your Blue Book search URL, then click **Restart URL from page 1**. This starts scraping immediately from page 1 even if the previous queue was complete. Prior jobs are archived; company records remain. Detected pagination is automatic.

**Start / Resume** keeps progress for the same URL. Entering a different URL switches the active queue to that search. **Stop & save** retains the current job for resume. Wait for the saved message before restarting or editing names.

**Edit company / contact name** lets you enter or correct names for a saved record using its exact profile_url from the export. Company name and public contact name/title are separate columns. Unknown owner names are not guessed. A later scrape may refresh manually edited values where the site supplies them.

For human verification, complete the check in the scraper's open browser, then click **Verification completed — Continue**. Hard access blocks cannot be bypassed. The app stops if verification remains after Continue.

Your supplied 2,012 records are included. If you collected newer results since uploading, close both apps and copy your latest progress.sqlite3 into this extracted folder before launching (keep a backup). Do not replace a newer database with the bundled older snapshot.

Ten offline tests passed, including restart, changing URL, resuming, data preservation and phone parsing. Windows and live-site execution remain unverified.

--- Previous phone-repair notes ---

# Updated Blue Book collector

Extract the entire ZIP into a new folder and double-click START.bat. Python 3.10+ with Tcl/Tk is required. The launcher installs dependencies and Chromium.

Your 2,012 saved company records and 473 existing phone-bearing records are preserved. The 1,539 profiles without a phone have been queued again. Click Start / Resume to process those profiles first. Do not click Retry missing phones repeatedly; it is available for a later deliberate recheck.

Phone detection now checks telephone links, metadata, labelled phone blocks and matching business JSON-LD. Fax-labelled blocks and Blue Book's support number are excluded. Company names are retained. Public contact names are captured only when explicitly marked as a Person; owner names cannot be inferred from a company name. Some numbers may still be unavailable or require markup not yet supported.

When an interactive robot check appears, the app leaves the browser open and pauses. Complete the check manually in that browser, then click Verification completed — Continue in the app. If the check remains, the app stops rather than retrying. Hard 403/access-denied pages stop immediately. No CAPTCHA bypass, proxy rotation, fingerprint evasion or automated challenge solving is included. A persistent dedicated browser_session folder retains this app's session locally; it is separate from your regular Chrome. Do not share that folder.

Stop & save retains progress. Exports are in exports/. Existing CSV and Excel files reflect your uploaded run until a new export completes. Close Excel before exporting. Missing fields stay blank. Jobs interrupted by a block remain pending. Resume skips completed jobs. Profiles are now processed before further listing pages so numbers arrive sooner.

Validation: eight offline tests passed for phone formats, metadata, JSON-LD company matching, exclusions, preserving existing data, pagination scope and resume behavior. Live Blue Book access and Windows execution were not available for verification, so this is an extractor repair, not a claim that the missing 1,539 phone numbers have already been recovered.

Coverage and seed configuration remain as in your supplied pack; see COVERAGE.md. This update does not certify every Pacific county or trade.
