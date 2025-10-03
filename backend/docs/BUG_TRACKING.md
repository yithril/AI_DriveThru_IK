# Bug Tracking Document

## Current Status: Voice AI Drive-Thru System

**Last Updated:** January 15, 2025  
**System Version:** Development/Demo - Major Bugs Resolved!

---

## 🎯 Working Features

✅ **Add single item** - Successfully adds one item to order  
✅ **Add multiple items** - Can add multiple items in one utterance  
✅ **Add items with modifications** - Can add items with customizations (e.g., "quantum burger with no onions")  
✅ **Remove items** - Can remove items from order  
✅ **Modify items** - Can modify existing items (quantity, size, ingredients)  
✅ **Answer questions** - Responds to customer questions about menu/restaurant  
✅ **Order total** - Provides total when customer wants to finish  
✅ **Clear order** - Can clear out entire order  
✅ **Validation** - Guards against too many items (MAX_TOTAL_ITEMS = 20)  
✅ **Performance logging** - Tracks timing for each step  
✅ **"Anything else?" prompt** - Asks follow-up question after adding items  

---

## 🐛 Outstanding Issues

### **Priority 1: Core Functionality**

*All core functionality bugs have been resolved! 🎉*

### **Priority 2: User Experience**

*All major UX bugs have been resolved! 🎉*

#### **BUG-007: Order Total Persists Between Sessions**
- **Description:** Order total from previous customer still shows on screen for new customer
- **Expected:** Screen should be cleared/reset when starting new session
- **Actual:** Previous order total remains visible
- **Impact:** Medium - Customer confusion, poor UX
- **Status:** 🔴 Open

#### **BUG-008: Error Messages Exposed to Customers**
- **Description:** When system errors occur, technical error messages are shown to customers instead of gentle fallback greetings
- **Expected:** System should fall back to standard gentle greeting on errors
- **Actual:** Technical error messages are exposed to customers
- **Impact:** Medium - Poor UX, jarring customer experience
- **Status:** 🔴 Open

#### **BUG-009: Speech-to-Text Accuracy Issues**
- **Description:** STT sometimes mishears menu item names (e.g., "meteor chicken" → "meatier chicken")
- **Expected:** STT should have access to menu context for better accuracy
- **Actual:** Basic Whisper API call without menu context or prompts
- **Impact:** Medium - Customer frustration, incorrect orders
- **Status:** 🔴 Open

#### **BUG-010: Car Controls Active During AI Processing** ✅ **RESOLVED**
- **Description:** "Next Car" button remains enabled while AI is processing or speaking
- **Expected:** Car controls should be disabled during AI processing/speaking to prevent state conflicts
- **Actual:** Users can click "Next Car" while AI is still processing, causing out-of-sync state
- **Impact:** High - State management issues, potential data corruption
- **Status:** ✅ **RESOLVED** - Added isAISpeaking check to disable car control buttons during AI processing

#### **BUG-011: Order Persists After New Session** ✅ **RESOLVED**
- **Description:** When clicking "New Session", the previous order still displays on screen
- **Expected:** Screen should be cleared and show empty order state for new customer
- **Actual:** Previous customer's order remains visible in the order component
- **Impact:** High - Customer confusion, incorrect order display
- **Status:** ✅ **RESOLVED** - Added useEffect to clear order data when sessionId changes

#### **BUG-012: Impossible Modifications Not Handled**
- **Description:** System doesn't gracefully handle requests for non-existent ingredients or impossible modifications
- **Example:** "I want a neon burger with two hockey sticks please" - hockey sticks don't exist as an ingredient
- **Expected:** System should politely inform customer that ingredient doesn't exist and suggest alternatives
- **Actual:** Unknown behavior - may fail silently or give confusing error
- **Impact:** Medium - Customer confusion, poor UX
- **Status:** 🔴 Open
- **Plan Needed:**
  - Define validation rules for ingredient existence
  - Create friendly error messages for impossible requests
  - Suggest similar/available ingredients as alternatives
  - Handle gracefully without breaking the order flow

#### **BUG-013: Modify Quantity of Non-Existent Order Item**
- **Description:** System incorrectly processes quantity modifications for items not in the current order
- **Example:** "I'd like 5 astro nuggets instead of 3" when astro nuggets isn't on the order
- **Expected:** System should clarify which item to modify or ask if they want to add astro nuggets
- **Actual:** System processes the modification as if the item exists in the order
- **Impact:** Medium - Customer confusion, incorrect order processing
- **Status:** 🔴 Open
- **Plan Needed:**
  - Validate that target item exists in current order before modification
  - Handle "instead of" phrasing for non-existent items
  - Clarify intent: modify existing item vs. add new item
  - Provide clear error messages for impossible modifications

---

## 🔧 Technical Debt & Improvements

### **Fuzzy Search Algorithm**
- Current fuzzy matching needs improvement
- Consider implementing better similarity scoring
- May need to adjust confidence thresholds

### **Modification Handling**
- Need to implement proper modification parsing
- Should capture and store modifications in order items
- Need to display modifications in order summary

### **Restaurant Information Service**
- Question agent needs access to restaurant service
- Should be able to answer hours, location, phone, etc.
- May need to add restaurant data to question context

### **Workflow Orchestration**
- Remove item workflow needs debugging
- Modify item workflow needs debugging
- May need to add performance timing to these workflows

---

## 📋 Next Steps

1. **Debug Remove Item Workflow**
   - Check if remove item workflow is being called
   - Verify order session service remove functionality
   - Test with simple remove commands

2. **Debug Modify Item Workflow**
   - Check if modify item workflow is being called
   - Verify modification parsing and storage
   - Test with simple modification commands

3. **Improve Fuzzy Search**
   - Review current fuzzy matching algorithm
   - Adjust similarity scoring
   - Test with various menu item names

4. **Add "Anything Else?" Prompt**
   - Modify add item workflow to include follow-up question
   - Ensure it only asks after successful item additions

5. **Fix Modifications**
   - Implement proper modification parsing
   - Store modifications in order items
   - Display modifications in order summary

---

## 🧪 Testing Scenarios

### **Remove Item Tests**
- [ ] "Remove the burger"
- [ ] "Take off the fries"
- [ ] "I don't want the drink"

### **Modify Item Tests**
- [ ] "Change the burger to no cheese"
- [ ] "Make the burger medium rare"
- [ ] "Add extra pickles to the burger"

### **Fuzzy Search Tests**
- [ ] "quantum burger" → should match "quantum cheeseburger"
- [ ] "cosmic fries" → should match "cosmic potato wedges"
- [ ] "space drink" → should match "space cola"

### **Modification Tests**
- [ ] "quantum cheeseburger with no cheese"
- [ ] "cosmic burger medium rare"
- [ ] "space fries extra crispy"

### **Restaurant Information Tests**
- [ ] "What are your hours?"
- [ ] "Where are you located?"
- [ ] "What's your phone number?"
- [ ] "What's your address?"

---

## 📊 Performance Notes

- **Total processing time:** ~8 seconds per voice input
- **Speech-to-text:** ~1.25 seconds
- **Intent classification:** ~0.8 seconds
- **Workflow execution:** ~0.3 seconds
- **Voice generation:** ~2.5 seconds
- **S3 upload:** ~1.5 seconds

---

## 🏷️ Labels

- `bug` - Confirmed bugs
- `enhancement` - Feature improvements
- `performance` - Performance related
- `ux` - User experience
- `core` - Core functionality
- `fuzzy-search` - Fuzzy matching issues
- `modifications` - Item modification handling
