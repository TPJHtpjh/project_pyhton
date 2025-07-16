// JavaScript 基本用法示例

// --- 数据类型 ---

// 1. 数字 (Number)
console.log(NaN); // Not a Number
console.log(Infinity); // 无穷大
console.log(0xff00); // 十六进制数

// 2. 布尔 (Boolean)
console.log(false == 0); // true, a==b 会进行类型转换
console.log(false === 0); // false, a===b 不会进行类型转换，要求类型和值都相等

// 3. 特殊数值
console.log(isNaN(NaN)); // true, isNaN() 用于检查一个值是否是 NaN

// 浮点数精度问题
console.log(1 / 3 === (1 - 2 / 3)); // false
// 比较浮点数是否相等，应该检查其差的绝对值是否小于一个很小的数
console.log(Math.abs(1 / 3 - (1 - 2 / 3)) < 0.0000001); // true

// 4. BigInt (大整数) - 用于表示大于 2^53 - 1 的整数
var bi1 = 9223372036854775807n;
var bi2 = BigInt(12345);
var bi3 = BigInt("0x7fffffffffffffff");
console.log(bi1 === bi2); // false
console.log(bi1 === bi3); // true
// console.log(1234567n + 3456789); // BigInt不能与Number混合运算, 会抛出 TypeError

// 5. 数组 (Array)
var arr = [1, 2, 3, 4.44, 'five', null, true];
console.log(arr[0]); // 1
console.log(arr[4]); // 'five'
console.log(arr[7]); // undefined, 索引越界

// --- 变量声明 ---
var a = 1; // 函数作用域，可以重复声明
let b = 2; // 块级作用域，不能重复声明
const c = 3; // 块级作用域，常量，声明时必须初始化，且不能重新赋值

// --- 字符串 (String) ---
let name = "Alice";
let greeting = `Hello, ${name}!`; // 模板字符串
console.log(greeting);
console.log(greeting.length); // 字符串长度
console.log(greeting.toUpperCase()); // 转为大写

// --- 对象 (Object) ---
let person = {
    firstName: "John",
    lastName: "Doe",
    age: 50,
    eyeColor: "blue",
    fullName: function () {
        return this.firstName + " " + this.lastName;
    }
};
console.log(person.firstName); // "John"
console.log(person.fullName()); // "John Doe"

// --- 控制流 ---

// if...else
let hour = new Date().getHours();
let timeOfDay;
if (hour < 12) {
    timeOfDay = "Morning";
} else if (hour < 18) {
    timeOfDay = "Afternoon";
} else {
    timeOfDay = "Evening";
}
console.log(`Good ${timeOfDay}!`);

// for 循环
for (let i = 0; i < arr.length; i++) {
    console.log(`Array element ${i} is ${arr[i]}`);
}

// for...of 循环 (ES6)
for (const element of arr) {
    console.log(element);
}

// --- 函数 (Function) ---

// 函数声明
function add(x, y) {
    return x + y;
}
console.log(add(5, 3)); // 8

// 箭头函数 (ES6)
const subtract = (x, y) => {
    return x - y;
};
console.log(subtract(5, 3)); // 2

const multiply = (x, y) => x * y; // 更简洁的写法
console.log(multiply(5, 3)); // 15

// --- 异步 JavaScript ---

// setTimeout
console.log("Start");
setTimeout(() => {
    console.log("This message is shown after 2 seconds");
}, 2000);
console.log("End");

// Promise
const myPromise = new Promise((resolve, reject) => {
    let success = true; // 模拟一个可能成功或失败的操作
    if (success) {
        resolve("Promise resolved successfully!");
    } else {
        reject("Promise rejected!");
    }
});

myPromise
    .then(result => console.log(result))
    .catch(error => console.log(error));

// async/await (ES2017)
async function fetchData() {
    try {
        // 模拟网络请求
        let response = await new Promise(resolve => setTimeout(() => resolve("Data fetched!"), 1000));
        console.log(response);
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}
fetchData(); 