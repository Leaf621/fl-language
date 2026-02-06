# Femboy Language Syntax

This document describes the core syntax shown in the example programs.

## Comments

- Single-line comments start with `#`.

## Imports

Use `adopt` to import modules.

```
adopt io
adopt utils.helper
```

Access imported modules with the `::` namespace operator.

```
utils::helper::greet("World")
```

## Variables and Constants

Declare variables with `keep`.

```
keep message = "hello"
keep number = 5
```

Use `share keep` to expose a symbol from a module.

```
share keep global_var = 5
```

## Functions

Functions use arrow syntax and can be shared.

```
keep add = (a, b) => {
	return a + b
}

share keep main = () => {
	io::print("Hello")
}
```

### Returning values

Use `return` inside a block.

```
keep getMessage = () => {
	return "hello world"
}
```

## Control Flow

### If / else if / else

```
if condition {
	io::print("true")
} else if otherCondition {
	io::print("else if")
} else {
	io::print("else")
}
```

### Loops

`go` iterates over lists.

```
keep lst = [1, "ok"]
go lst by x {
	io::print(x)
}
```

`stay` is a while-like loop.

```
keep i = 0
stay i < 5 {
	i += 1
}
```

### Ranges

Use `to` to build a range.

```
keep range = 0 to 3
```

## Classes and Inheritance

Define classes with `boy`.

```
keep Human = boy {
	share keep name = ""
	keep privateAge = 0

	share keep born = (self, age) => {
		self.privateAge = age
	}

	share keep talk = (self) => {
		io::print("Hi, I am", self.name)
	}
}
```

Inheritance uses `boy : Parent`.

```
keep Cutie = boy : Human {
	share keep born = (self, age) => {
		daddy(age)
	}

	share keep talk = (self, age) => {
		daddy.talk()
		io::print("...and I am cute!")
	}
}
```

Inside overrides, call the parent with `daddy`.

## Object Creation

Use `makeout` to create instances.

```
keep h = makeout Human(18)
h.name = "Alex"
```

## Booleans and Logic

```
keep alwaysTrue = YES
keep alwaysFalse = NO
if !alwaysTrue {
	io::print("false branch")
} else if alwaysFalse {
    io::print("false branch")
} else {
    io::print("true branch")
}
```

## Lists

```
keep lst = [1, "okak"]
```

## Native Code (JS Interop)

Mark a variable as native and assign inside a `native => { ... }` block.

```
keep jsAlert = (message) => {
	keep result: native
	native => {
		result = String(message).toUpperCase()
	}
	return result
}
```

## Variadic Functions

Use `rest...` to capture extra arguments.

```
keep varargFn = (first, rest...) => {
	io::print("First:", first)
	go rest by item {
		io::print("Rest item:", item)
	}
}
```

## Program Entry

Call your `main` function at the end of the file.

```
main()
```
