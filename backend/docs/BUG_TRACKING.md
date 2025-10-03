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
✅ **Order archiving** - Completed orders are saved to PostgreSQL database  
✅ **Button state management** - "New Car" and "Next Customer" buttons properly disabled during API processing and AI speaking  
✅ **Item consolidation** - Duplicate identical items are consolidated with combined quantities  
✅ **Session management** - Prevents race conditions and session conflicts during processing  
✅ **Negative quantity validation** - Prevents adding negative quantities to orders  
✅ **Menu item validation** - Only allows adding items that exist in the restaurant's menu  
✅ **Ingredient validation** - Only allows modifications with ingredients that exist in the menu system  

---

## Outstanding Issues


#### **BUG-008: Error Messages Exposed to Customers**
- **Description:** When system errors occur, technical error messages are shown to customers instead of gentle fallback greetings
- **Expected:** System should fall back to standard gentle greeting on errors
- **Actual:** Technical error messages are exposed to customers
- **Impact:** Medium - Poor UX, jarring customer experience
- **Status:**  Open



#### **BUG-012: Impossible Modifications Not Handled**
- **Description:** System doesn't gracefully handle requests for non-existent ingredients or impossible modifications
- **Example:** "I want a neon burger with two hockey sticks please" - hockey sticks don't exist as an ingredient
- **Expected:** System should politely inform customer that ingredient doesn't exist and suggest alternatives
- **Actual:** Unknown behavior - may fail silently or give confusing error
- **Impact:** Medium - Customer confusion, poor UX
- **Status:**  Open
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
- **Status:**  Open
- **Plan Needed:**
  - Validate that target item exists in current order before modification
  - Handle "instead of" phrasing for non-existent items
  - Clarify intent: modify existing item vs. add new item
  - Provide clear error messages for impossible modifications


#### **BUG-016: AI Response Missing Item Modifications**
- **Description:** When AI confirms adding items, it doesn't mention the modifications (e.g., "extra cheese")
- **Example:** Customer says "quantum burger with extra cheese" → AI responds "Added Quantum Cheeseburger" (missing "with extra cheese")
- **Expected:** AI should mention modifications in confirmation: "Added Quantum Cheeseburger with extra cheese"
- **Actual:** AI only mentions base item name, ignoring customizations
- **Impact:** Medium - Poor user experience, customers can't verify their modifications were understood
- **Status:** 🔄 **PENDING**
- **Plan Needed:**
  - Update AI response generation to include modification details
  - Ensure modifications are passed to response generation
  - Test with various modification types

---

## 🔧 Technical Debt & Improvements

### **Fuzzy Search Algorithm** ✅ **RESOLVED**
- ~~Current fuzzy matching needs improvement~~ → **FIXED**: Fuzzy search working well with rapidfuzz
- ~~Consider implementing better similarity scoring~~ → **IMPLEMENTED**: Using WRatio scorer with 60+ score threshold
- ~~May need to adjust confidence thresholds~~ → **OPTIMIZED**: Current thresholds working effectively

### **Modification Handling** ✅ **RESOLVED**
- ~~Need to implement proper modification parsing~~ → **IMPLEMENTED**: Modifications properly parsed and stored
- ~~Should capture and store modifications in order items~~ → **IMPLEMENTED**: Modifications stored in order items with normalization
- ~~Need to display modifications in order summary~~ → **IMPLEMENTED**: AI responses now include modifications in confirmations

### **Restaurant Information Service** ✅ **RESOLVED**
- ~~Question agent needs access to restaurant service~~ → **IMPLEMENTED**: Restaurant service integrated
- ~~Should be able to answer hours, location, phone, etc.~~ → **IMPLEMENTED**: All restaurant info queries working
- ~~May need to add restaurant data to question context~~ → **IMPLEMENTED**: Restaurant data properly populated and accessible

### **Workflow Orchestration** ✅ **MOSTLY RESOLVED**
- ~~Remove item workflow needs debugging~~ → **WORKING**: Remove item workflow functional
- ~~Modify item workflow needs debugging~~ → **WORKING**: Modify item workflow functional  
- ~~May need to add performance timing to these workflows~~ → **IMPLEMENTED**: Performance timing added to all workflows

### **Upselling System**
- **Future Enhancement:** Implement intelligent upselling recommendations
- **Features to Add:**
  - Suggest complementary items based on current order (e.g., "Would you like fries with that burger?")
  - Recommend premium upgrades (e.g., "Upgrade to large size for just $1 more?")
  - Suggest popular add-ons (e.g., "Add a drink to complete your meal?")
  - Seasonal/promotional item suggestions
- **Implementation Approach:**
  - Create upselling agent that analyzes current order context
  - Build recommendation engine based on menu item relationships
  - Add upselling prompts to order completion workflow
  - Track upselling success rates and optimize recommendations

### **Intelligent Dietary Analysis System**
- **Future Enhancement:** AI-powered dietary restriction analysis and recommendations
- **Features to Add:**
  - Ingredient-level dietary flags (gluten-free, vegan, vegetarian, keto, sugar-free, etc.)
  - Dynamic menu item analysis based on modifications
  - AI responses to dietary questions ("What's gluten-free?", "What's vegan?")
  - Smart dietary recommendations ("Remove the bun to make it keto")
  - Allergen and dietary conflict detection
- **Implementation Approach:**
  - Add dietary fields to Ingredient model (is_gluten_free, is_vegan, is_keto, etc.)
  - Create dietary analysis service to evaluate menu items + modifications
  - Enhance question agent with dietary knowledge
  - Add dietary filtering to menu search
  - Implement dynamic dietary status calculation (e.g., "This burger becomes keto if you remove the bun")

---

## 📋 Next Steps

1. ✅ **Debug Remove Item Workflow** - **COMPLETED**
   - ~~Check if remove item workflow is being called~~ → **WORKING**
   - ~~Verify order session service remove functionality~~ → **VERIFIED**
   - ~~Test with simple remove commands~~ → **TESTED**

2. ✅ **Debug Modify Item Workflow** - **COMPLETED**
   - ~~Check if modify item workflow is being called~~ → **WORKING**
   - ~~Verify modification parsing and storage~~ → **VERIFIED**
   - ~~Test with simple modification commands~~ → **TESTED**

3. ✅ **Improve Fuzzy Search** - **COMPLETED**
   - ~~Review current fuzzy matching algorithm~~ → **OPTIMIZED**
   - ~~Adjust similarity scoring~~ → **IMPLEMENTED**
   - ~~Test with various menu item names~~ → **TESTED**

4. ✅ **Add "Anything Else?" Prompt** - **COMPLETED**
   - ~~Modify add item workflow to include follow-up question~~ → **IMPLEMENTED**
   - ~~Ensure it only asks after successful item additions~~ → **WORKING**

5. ✅ **Fix Modifications** - **COMPLETED**
   - ~~Implement proper modification parsing~~ → **IMPLEMENTED**
   - ~~Store modifications in order items~~ → **IMPLEMENTED**
   - ~~Display modifications in order summary~~ → **IMPLEMENTED**

### **Current Priority Items:**
1. **Resolve Outstanding Bugs** - Focus on BUG-008, BUG-012, BUG-013, BUG-016
2. **Performance Optimization** - Continue monitoring and optimizing response times
3. **Future Enhancements** - Implement upselling and dietary analysis systems

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

---

## 🚀 Future Improvements

#### **FEATURE-001: Auto-Archive Orders on Next Customer**
- **Description:** Automatically archive orders when "Next Customer" is clicked, even if customer didn't explicitly confirm
- **Business Case:** Some customers drive off without confirming, but order data is still valuable for analytics and potential recovery
- **Implementation Plan:**
  - Create `/api/sessions/archive-current-order` endpoint
  - Update CarControlComponent to archive before clearing session
  - Add order status tracking: "pending" (auto-archived) vs "confirmed" (explicitly confirmed)
  - Consider confirmation dialog: "Customer drove off - archive order?"
- **Priority:** Low - Other pressing issues take precedence
- **Status:** 📋 **PLANNED**
