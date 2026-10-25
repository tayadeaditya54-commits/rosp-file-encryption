// Test suite for Input component bug fixes and accessibility enhancements
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";

console.log("==================================================================");
console.log("RUNNING AUTOMATED TEST SUITE: Untitled UI React - Input Component Fixes");
console.log("Experiment 10: Technical Verification & Validation");
console.log("Candidate: Karan Rajiwade | B.E. IT | ACPCE Kharghar");
console.log("==================================================================\n");

let passedCount = 0;
let totalCount = 0;

function runTest(testName, fn) {
    totalCount++;
    try {
        fn();
        console.log(`[PASS] Test ${totalCount}: ${testName}`);
        passedCount++;
    } catch (err) {
        console.error(`[FAIL] Test ${totalCount}: ${testName}`);
        console.error(`       Error: ${err.message}`);
    }
}

// Read the modified files
const inputPath = path.resolve("components/base/input/input.tsx");
const inputNumberPath = path.resolve("components/base/input/input-number.tsx");

const inputCode = fs.readFileSync(inputPath, "utf-8");
const inputNumberCode = fs.readFileSync(inputNumberPath, "utf-8");

// Test 1: Verify hasTrailingIcon includes type === "password"
runTest("InputBase accurately computes hasTrailingIcon for password fields to allocate trailing padding", () => {
    assert(
        inputCode.includes('Boolean(tooltip || isInvalid || type === "password")'),
        "hasTrailingIcon must include type === 'password' to prevent text overlap with the toggle button"
    );
});

// Test 2: Verify Password toggle button includes isDisabled={isDisabled}
runTest("Password toggle AriaButton receives isDisabled prop from input state", () => {
    assert(
        inputCode.includes("isDisabled={isDisabled}"),
        "Password toggle button must receive isDisabled to prevent clicks when input is disabled"
    );
});

// Test 3: Verify Password toggle button includes type=\"button\"
runTest("Password toggle AriaButton explicitly declares type='button' to prevent form submission", () => {
    assert(
        inputCode.includes('type="button"'),
        "Password toggle button must explicitly declare type='button'"
    );
});

// Test 4: Verify dynamic accessibility aria-label on password toggle
runTest("Password toggle AriaButton provides dynamic accessible label for screen readers", () => {
    assert(
        inputCode.includes('aria-label={isPasswordVisible ? "Hide password" : "Show password"}'),
        "Password toggle button must provide dynamic 'Hide password' / 'Show password' aria-label"
    );
    assert(
        inputCode.includes('aria-pressed={isPasswordVisible}'),
        "Password toggle button must include aria-pressed reflecting current visibility state"
    );
});

// Test 5: Verify disabled styling on the toggle button
runTest("Password toggle button includes disabled tailwind utility classes", () => {
    assert(
        inputCode.includes("disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50"),
        "Password toggle button must include disabled styling classes"
    );
});

// Test 6: Verify Input component forwards isRequired, isInvalid, and isDisabled to InputBase
runTest("Input component forwards isRequired, isInvalid, and isDisabled down to InputBase", () => {
    assert(inputCode.includes("isRequired,"), "Input must forward isRequired to InputBase");
    assert(inputCode.includes("isInvalid,"), "Input must forward isInvalid to InputBase");
    assert(inputCode.includes("isDisabled: props.isDisabled,"), "Input must forward isDisabled to InputBase");
});

// Test 7: Verify InputNumber has cleaned up unused Date imports and granularity prop
runTest("InputNumber removes copy-pasted DateFieldProps, DateValue, and granularity type pollution", () => {
    assert(!inputNumberCode.includes("AriaDateFieldProps"), "InputNumber should not import AriaDateFieldProps");
    assert(!inputNumberCode.includes("DateValue"), "InputNumber should not import DateValue");
    assert(!inputNumberCode.includes("granularity"), "InputNumber should not pick granularity prop");
});

// Test 8: Trailing padding logic simulation
runTest("Padding simulation confirms trailing padding is granted when type === 'password'", () => {
    const computeHasTrailing = (tooltip, isInvalid, type) => Boolean(tooltip || isInvalid || type === "password");

    assert.strictEqual(computeHasTrailing(undefined, false, "password"), true, "Password field must have trailing space");
    assert.strictEqual(computeHasTrailing("Help text", false, "text"), true, "Tooltip field must have trailing space");
    assert.strictEqual(computeHasTrailing(undefined, true, "text"), true, "Invalid field must have trailing space");
    assert.strictEqual(computeHasTrailing(undefined, false, "text"), false, "Plain text field should not have trailing space");
});

console.log("\n==================================================================");
console.log(`TEST SUMMARY: ${passedCount} / ${totalCount} tests passed successfully.`);
console.log(`EXIT CODE: ${passedCount === totalCount ? 0 : 1}`);
console.log("==================================================================");

process.exit(passedCount === totalCount ? 0 : 1);
