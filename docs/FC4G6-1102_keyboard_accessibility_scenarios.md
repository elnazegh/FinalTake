# FC4G6-1102 — Keyboard Accessibility Test Scenarios

**Project:** FinalTake — Sprint 5
**Preparation Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Base Revision:** 2475dd1

## Test Environment

- Local FinalTake frontend and Flask backend
- Google Chrome on macOS
- macOS Keyboard Navigation enabled
- Keyboard-only input: Tab, Shift+Tab, Enter, Space, and arrow keys
- Sample query: Dark
- Sample media: The Dark Knight (Media ID 1)

## Test Scenarios

| ID | Scenario | Expected Result |
|---|---|---|
| K1 | Navigate to the search field and submit Dark using the keyboard | Four matching results appear |
| K2 | Select Movies and Release Year: Newest First using the keyboard | Two movie results appear in correct order |
| K3 | Navigate to The Dark Knight result and open Media Details using Enter | Correct details page opens without a mouse |
| K4 | Check focus visibility, logical Tab order, Shift+Tab, and Back to Search navigation | Interactive controls remain reachable and visibly focused |

## Testing Procedure

1. Open FinalTake in Chrome.
2. Use Tab to reach the search field.
3. Type Dark and submit using the keyboard.
4. Use the keyboard to select Movies and Release Year: Newest First.
5. Submit the search and verify the result order.
6. Tab to The Dark Knight result and press Enter.
7. Use the keyboard to activate Back to Search.
8. Check focus visibility, navigation order, and keyboard traps throughout.

## Verification Guidelines

- Use no mouse during the actual test workflow.
- Native dropdown keyboard behavior may vary by browser.
- Confirm any unexpected behavior before classifying it as a defect.
- Record actual observations and supporting screenshots in FC4G6-1103 and FC4G6-1104.
- Coordinate identified frontend accessibility issues with the Frontend/UX developer.

## Scope

This plan covers basic keyboard accessibility for search and media navigation. It is not a full WCAG accessibility audit.

No application code changes are required to prepare these scenarios.
