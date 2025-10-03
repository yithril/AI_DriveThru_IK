# QA Testing Plan - AI Drive-Thru System

**Last Updated:** October 3, 2025  
**System Version:** Production Ready - Context Resolution & Menu Matching Fixed!

---

## 🎯 **HAPPY PATH TESTS** (Core Functionality)

### **✅ Basic Ordering Flow**
- [ ] **Single item order:** "I'll take a quantum cheeseburger"
- [ ] **Multiple items:** "I'll take a quantum cheeseburger and galactic fries"
- [ ] **Item with modifications:** "Quantum cheeseburger with extra cheese"
- [ ] **Multiple items with different modifications:** "Quantum cheeseburger with extra cheese and veggie wrap with no onions"

### **✅ Context Resolution (NEW!)**
- [ ] **Pronoun resolution:** "What's on the veggie wrap?" → "Cool, I'll take two of those"
- [ ] **Recent item reference:** "Actually, take those off" (removes only recently added items)
- [ ] **Question → Order flow:** "What's on the quantum burger?" → "I'll take one of those"

### **✅ Order Management**
- [ ] **Remove specific item:** "Take off the galactic fries"
- [ ] **Modify existing item:** "Make that quantum cheeseburger extra cheese"
- [ ] **Update quantity:** "Make that 3 quantum cheeseburgers"
- [ ] **Clear entire order:** "Actually, clear my order"

### **✅ Order Completion**
- [ ] **Confirm order:** "That's everything"
- [ ] **Check order summary:** Verify all items and modifications
- [ ] **Database persistence:** Verify order saved to PostgreSQL

---

## 🚨 **EDGE CASE TESTS** (Error Handling)

### **❌ Invalid Items (NEW 70% Threshold)**
- [ ] **Completely unrelated items:** "I'd like foie gras" → "Sorry, we don't have that"
- [ ] **Fancy restaurant items:** "I'll take truffles and caviar" → Proper rejection
- [ ] **Mixed valid/invalid:** "Quantum cheeseburger and lobster" → Add valid, reject invalid

### **❌ Ambiguous Items**
- [ ] **Multiple similar items:** "I'll take a burger" → "Which burger? We have Quantum Cheeseburger, Neon Double Burger..."
- [ ] **Partial names:** "I'll take the quantum" → Should ask for clarification

### **❌ Invalid Modifications**
- [ ] **Non-existent ingredients:** "Quantum cheeseburger with truffles" → Reject modification
- [ ] **Conflicting modifications:** "Extra cheese, no cheese" → Handle gracefully

### **❌ Edge Quantities**
- [ ] **Excessive quantity:** "I'll take 100 quantum cheeseburgers" → Reject or limit
- [ ] **Negative quantity:** "I'll take -2 quantum cheeseburgers" → Reject
- [ ] **Zero quantity:** "Make that 0 quantum cheeseburgers" → Remove item

---

## 🧠 **CONTEXT & CONVERSATION TESTS**

### **✅ Multi-Turn Conversations**
- [ ] **Question → Order:** "What's on the veggie wrap?" → "I'll take two"
- [ ] **Order → Modify:** "Quantum cheeseburger" → "Actually, make that extra cheese"
- [ ] **Order → Remove:** "I'll take fries" → "Actually, take those off"

### **✅ Pronoun Resolution**
- [ ] **"That one":** "What's on the quantum burger?" → "I'll take that one"
- [ ] **"Those":** "I'll take two veggie wraps" → "Actually, take those off"
- [ ] **"It":** "What's on the salad?" → "I'll take it"

### **✅ Context Switching**
- [ ] **Item A → Question about B → Order B:** "Quantum burger" → "What's on the wrap?" → "I'll take the wrap"
- [ ] **Multiple items → Remove specific:** "Burger and fries" → "Take off the burger"

---

## 🎤 **NATURAL SPEECH TESTS**

### **✅ Background Noise**
- [ ] **Phone conversation:** "I'll take a burger...hold on...yeah, a quantum cheeseburger"
- [ ] **Passenger chatter:** "I'll take fries...stop hitting your sister...and a drink"
- [ ] **Corrections:** "I'll take 2 burgers...no wait...make that 3"

### **✅ Unclear Speech**
- [ ] **Mumbling:** "I'll take a...um...quantum thing"
- [ ] **Interruptions:** "I'll take a quantum...what was that? ...cheeseburger"
- [ ] **Fast speech:** Rapid-fire ordering

---

## 🔧 **SYSTEM INTEGRATION TESTS**

### **✅ Button States**
- [ ] **"New Car" button:** Disabled during AI processing
- [ ] **"Next Customer" button:** Disabled during AI processing
- [ ] **Microphone button:** Shows loading state during processing

### **✅ Order Display**
- [ ] **Item consolidation:** Same items with same modifications show as quantity
- [ ] **Modifier costs:** Extra cheese shows additional cost
- [ ] **Order totals:** Subtotal, tax, total calculated correctly

### **✅ Database Operations**
- [ ] **Order archiving:** Orders saved to PostgreSQL after completion
- [ ] **Session management:** New car clears previous order
- [ ] **Conversation history:** Context maintained across turns

---

## 🚀 **PERFORMANCE TESTS**

### **✅ Response Times**
- [ ] **Simple order:** < 3 seconds
- [ ] **Complex order:** < 5 seconds
- [ ] **Context resolution:** < 4 seconds
- [ ] **Question answering:** < 3 seconds

### **✅ Memory Usage**
- [ ] **Large orders:** 10+ items with modifications
- [ ] **Long conversations:** 20+ turns
- [ ] **Multiple sessions:** Concurrent users

---

## 📋 **TESTING CHECKLIST**

### **Pre-Test Setup**
- [ ] Clear database
- [ ] Fresh browser session
- [ ] Check all services running
- [ ] Verify menu data loaded

### **Test Execution**
- [ ] Test each scenario 3 times
- [ ] Note any failures or unexpected behavior
- [ ] Check database after each test
- [ ] Verify frontend display matches backend

### **Post-Test Cleanup**
- [ ] Clear test data
- [ ] Reset to clean state
- [ ] Document any issues found

---

## 🎯 **SUCCESS CRITERIA**

**System is ready for production if:**
- ✅ All Happy Path tests pass
- ✅ All Edge Case tests handle gracefully (no crashes)
- ✅ Context Resolution works for 80%+ of scenarios
- ✅ Response times under 5 seconds
- ✅ Database persistence works
- ✅ UI states work correctly

---

## 🏷️ **Test Categories**

- `happy-path` - Core functionality that should work
- `edge-case` - Error scenarios that should be handled gracefully  
- `context` - Conversation and pronoun resolution
- `performance` - Speed and memory usage
- `integration` - System components working together
