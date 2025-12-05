# Phase 2D Testing Checklist

**Date:** December 5, 2025
**Status:** Ready for Testing
**Branch:** `claude/phase-2-audio-pipeline-01P9wi8j7BoYqtkNEsPDNbLL`

---

## ✅ Pre-Testing Verification (DONE)

- ✅ Git status clean - all changes committed and pushed
- ✅ All 9 React components created
- ✅ All 4 CSS stylesheets created
- ✅ Backend API endpoints added
- ✅ Python 3.11.14 installed
- ✅ Required Python packages installed (FastAPI, uvicorn, redis)
- ✅ Redis server available
- ✅ All imports verified in App.jsx

---

## 🔧 Setup Steps (Do First)

### 1. Install Frontend Dependencies
```bash
cd /home/user/freya_v2/src/gui/frontend
npm install
```

**Expected result:**
- `node_modules/` directory created
- No errors during installation

### 2. Start Redis (if not running)
```bash
redis-server &
# Or check if already running:
redis-cli ping
# Should respond: PONG
```

### 3. Start Backend Server
```bash
cd /home/user/freya_v2
python -m src.main
```

**Expected output:**
- Services starting (GUI, TTS, STT, Audio Manager)
- GUI Service message: `✓ GUI Service started on http://localhost:8000`
- No errors

**If errors occur:**
- Check Redis is running
- Check port 8000 is available
- Check config.yaml settings

### 4. Start Frontend Dev Server
```bash
# In a new terminal
cd /home/user/freya_v2/src/gui/frontend
npm run dev
```

**Expected output:**
- Vite dev server starting
- Message: `Local: http://localhost:5173/`
- No compilation errors

### 5. Open Browser
```
http://localhost:5173
```

---

## 🧪 Testing Checklist

### **Tab Navigation (Home Tab)**
- [ ] Page loads without errors
- [ ] Header shows "Freya v2.0 Dashboard"
- [ ] 5 tabs visible: Home, Audio, Debug, Tests, Tools
- [ ] Home tab is active (blue underline)

### **Service Status Cards**
- [ ] Service cards display on left panel
- [ ] Each card shows:
  - [ ] Service name
  - [ ] Health indicator (green/yellow/red dot with pulse)
  - [ ] Status badge (Running/Stopped/etc)
  - [ ] Uptime (format: XXh XXm or XXd XXh)
  - [ ] Error count
  - [ ] "Memory: N/A" (placeholder)
  - [ ] "Requests: 0/sec" (placeholder)
- [ ] Cards have hover effect (lift up slightly)

### **Chat Interface**
- [ ] Chat panel on right side
- [ ] "Conversation" header visible
- [ ] Empty state or existing messages shown
- [ ] Chat input box at bottom
- [ ] "Send" button visible
- [ ] Connection status in bottom-right: "Connected" (green dot)

### **Theme Toggle**
- [ ] Sun/Moon button in header (top-right)
- [ ] Click toggles between dark and light mode
- [ ] ALL colors change smoothly (0.3s transition)
- [ ] Text remains readable in both modes
- [ ] Status dots remain visible in both modes

### **Keyboard Shortcuts**
- [ ] `Ctrl+1` switches to Home tab
- [ ] `Ctrl+2` switches to Audio tab
- [ ] `Ctrl+3` switches to Debug tab
- [ ] `Ctrl+4` switches to Tests tab
- [ ] `Ctrl+5` switches to Tools tab
- [ ] `Ctrl+D` switches to Debug tab
- [ ] `Ctrl+T` switches to Tests tab

---

### **Audio Tab**
- [ ] Click Audio tab (or press Ctrl+2)
- [ ] Page loads without errors

**Device Selection:**
- [ ] "Audio Devices" section visible
- [ ] "Placeholder data" badge shown
- [ ] Input device dropdown shows 3 devices:
  - [ ] Default Microphone (Default)
  - [ ] USB Microphone
  - [ ] Webcam Microphone
- [ ] Output device dropdown shows 3 devices:
  - [ ] Default Speaker (Default)
  - [ ] Headphones
  - [ ] HDMI Audio
- [ ] Dropdowns are functional

**Microphone Test:**
- [ ] "Microphone Test" section visible
- [ ] "Start Recording" button visible
- [ ] Click button changes to "Stop Recording"
- [ ] Volume meter animates with random levels
- [ ] 12 colored bars (green → yellow → red)
- [ ] Level percentage displays (0-100%)
- [ ] "Visual demo only" note appears
- [ ] Recording indicator shows with pulse dot
- [ ] Stop button stops animation

**TTS Test:**
- [ ] "Text-to-Speech Test" section visible
- [ ] "Feature coming soon!" badge shown
- [ ] Text input box accepts text
- [ ] "Generate Speech" button visible
- [ ] Click shows "Generating..." with spinner (1 second)
- [ ] Result shows: "TTS testing coming soon!"
- [ ] Info badge appears

**Info Box:**
- [ ] Info box at bottom with 4 bullet points
- [ ] Text readable and properly formatted

---

### **Debug Tab**
- [ ] Click Debug tab (or press Ctrl+3)
- [ ] Page loads without errors

**Controls:**
- [ ] Channel filter dropdown visible
- [ ] "All Channels" selected by default
- [ ] Search input box visible
- [ ] Pause button (⏸️) visible
- [ ] Auto-scroll checkbox visible (checked)
- [ ] Clear button visible
- [ ] Export button visible

**Stats Bar:**
- [ ] Total count shows
- [ ] Filtered count shows
- [ ] Channels count shows

**Message List:**
- [ ] Messages appear in real-time as backend sends them
- [ ] Each message card shows:
  - [ ] Color-coded channel dot
  - [ ] Channel name
  - [ ] Timestamp (HH:MM:SS.mmm format)
  - [ ] Copy button (📋)
  - [ ] Expand button (▶)
- [ ] Click message expands to show full data
- [ ] JSON formatted nicely
- [ ] Copy button copies to clipboard

**Functionality:**
- [ ] Type in search box filters messages
- [ ] Select channel filters by channel
- [ ] Pause button stops new messages
- [ ] Resume button (▶️) restarts messages
- [ ] Clear button empties message list
- [ ] Export button downloads JSON file
- [ ] Auto-scroll keeps latest message visible

---

### **Tests Tab**
- [ ] Click Tests tab (or press Ctrl+4)
- [ ] Page loads without errors

**Test Controls:**
- [ ] "Test Suite Runner" section visible
- [ ] "Mock results" badge shown
- [ ] Suite dropdown shows:
  - [ ] All Tests
  - [ ] Unit Tests Only
  - [ ] Integration Tests Only
- [ ] "Run Tests" button visible with ▶️ icon

**Run Test Suite:**
- [ ] Click "Run Tests" button
- [ ] Button changes to "Running Tests..." with spinner
- [ ] Progress bar appears (0% → 100%)
- [ ] Progress percentage updates smoothly
- [ ] Takes ~2 seconds to complete

**Test Results:**
- [ ] Results section appears after completion
- [ ] 4 summary cards show:
  - [ ] Total: 52
  - [ ] Passed: 43 (green)
  - [ ] Failed: 0 (red)
  - [ ] Skipped: 9 (yellow)
- [ ] Pass Rate bar shows: 82% (green/yellow gradient)
- [ ] Suite, Duration, and Status metadata visible
- [ ] "Show Detailed Results" button visible
- [ ] Click expands to show test details
- [ ] Passed tests list visible
- [ ] Skipped tests list visible

**Coverage Visualization:**
- [ ] "Code Coverage" section visible
- [ ] "Placeholder data" badge shown
- [ ] Circular progress shows 15.62%
- [ ] Quality rating: "Needs Improvement" (red/orange)
- [ ] Module list shows 6 modules
- [ ] Each module has:
  - [ ] File name
  - [ ] Percentage (color-coded)
  - [ ] Progress bar
- [ ] 3 stat cards at bottom:
  - [ ] Modules Tested: 6
  - [ ] Code Coverage: 15.62%
  - [ ] Quality Rating: Low

---

### **Tools Tab**
- [ ] Click Tools tab (or press Ctrl+5)
- [ ] Page loads without errors
- [ ] "MCP Tool Calls History" header visible

**Empty State:**
- [ ] If no tool calls: "No tool calls yet" shown

**With Tool Calls:**
- [ ] Each tool card shows:
  - [ ] Tool name (blue text)
  - [ ] Success/Error badge (green/red)
  - [ ] Duration in seconds
  - [ ] Error message if failed
- [ ] Cards have hover effect
- [ ] Last 20 tools shown (newest first)

---

## 🎨 Visual Quality Check

### **Layout & Spacing**
- [ ] No overlapping elements
- [ ] Consistent padding/margins throughout
- [ ] Cards aligned properly in grids
- [ ] Text doesn't overflow containers

### **Colors & Contrast**
- [ ] All text readable in dark mode
- [ ] All text readable in light mode
- [ ] Status colors clearly distinct:
  - [ ] Green = healthy/success
  - [ ] Yellow = warning
  - [ ] Red = error/critical
  - [ ] Gray = placeholder/inactive
  - [ ] Blue = info/interactive

### **Animations**
- [ ] Smooth transitions (no janky movements)
- [ ] Pulse animations on health dots
- [ ] Volume meter animates smoothly
- [ ] Progress bars fill smoothly
- [ ] Hover effects work consistently

### **Typography**
- [ ] Headers clearly hierarchy (h1 > h2 > h3)
- [ ] Body text readable size
- [ ] Monospace font for code/data
- [ ] No text cutoff or ellipsis issues

---

## 📱 Responsive Design Testing

### **Desktop (1200px+)**
- [ ] Two-column layout on Home tab
- [ ] Service cards in grid (multiple columns)
- [ ] All content fits without horizontal scroll

### **Tablet (768px - 1200px)**
- [ ] Single column layout on Home tab
- [ ] Service cards still in grid
- [ ] Navigation tabs scrollable if needed

### **Mobile (< 768px)**
- [ ] Single column everywhere
- [ ] Tabs scroll horizontally
- [ ] Buttons full-width
- [ ] Touch-friendly tap targets
- [ ] No horizontal overflow

**Test by resizing browser window**

---

## ⚠️ Error Handling Testing

### **Test Error Boundary**
To test error boundary, you can temporarily break a component:

1. Open browser DevTools Console
2. Type: `window.testError = () => { throw new Error('Test error') }`
3. Call this in a component render

**Expected:**
- [ ] Error boundary catches the error
- [ ] Fallback UI displays with warning icon
- [ ] Error message shown: "An unexpected error occurred"
- [ ] "Try Again" button visible
- [ ] "Reload Page" button visible
- [ ] Click "Try Again" recovers
- [ ] No console spam

---

## 🐛 Known Issues / Expected Behavior

### **Placeholders (Not Bugs):**
- ✓ Audio devices are mock data (expected)
- ✓ TTS returns "coming soon" (expected)
- ✓ Test results are mock (expected)
- ✓ Coverage data from Phase 2 (expected)
- ✓ Memory/Request metrics show "N/A" (expected)

### **Backend Dependencies:**
- ⚠️ Service cards only show if backend is running
- ⚠️ Debug panel only shows messages if services are active
- ⚠️ Chat requires backend WebSocket connection

---

## ✅ Success Criteria

**All tests pass if:**
- ✅ All 5 tabs load without errors
- ✅ Theme toggle works in all tabs
- ✅ Keyboard shortcuts work
- ✅ No console errors (check DevTools)
- ✅ Responsive design works on mobile
- ✅ Placeholder features clearly marked
- ✅ Real features work with backend
- ✅ Error boundary catches errors
- ✅ Smooth animations throughout

---

## 🔍 Browser Console Check

Open DevTools (F12) and check:
- [ ] No red errors in Console tab
- [ ] No 404 errors in Network tab
- [ ] WebSocket connection established (ws://localhost:8000/ws)
- [ ] React DevTools shows component tree

---

## 📊 Performance Check

- [ ] Initial page load < 2 seconds
- [ ] Tab switching instant (< 100ms)
- [ ] Theme toggle smooth (< 300ms)
- [ ] No lag when typing in inputs
- [ ] Animations at 60fps

---

## 🎉 If All Tests Pass

**Phase 2D is PRODUCTION READY!**

Next steps:
1. ✅ Merge branch to main
2. ✅ Deploy to staging/production
3. ✅ Gather user feedback
4. 🔧 Wire placeholder features to real backends
5. 📈 Add more features as needed

---

## 🆘 Troubleshooting

### **Frontend won't start:**
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### **Backend errors:**
```bash
# Check Redis
redis-cli ping

# Check logs
tail -f logs/*.log

# Restart backend
# Ctrl+C to stop, then:
python -m src.main
```

### **Port already in use:**
```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### **WebSocket not connecting:**
- Check backend is running
- Check browser console for errors
- Verify URL is ws://localhost:8000/ws
- Check firewall/antivirus settings

---

**Testing Date:** _______________
**Tester Name:** _______________
**Pass/Fail:** _______________
**Notes:** _______________________________________________
