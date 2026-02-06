# Синтаксис языка Femboy

Этот документ описывает базовый синтаксис, показанный в примерах программ.

## Комментарии

- Однострочные комментарии начинаются с `#`.

## Импорты

Используйте `adopt`, чтобы импортировать модули.

```
adopt io
adopt utils.helper
```

Доступ к импортированным модулям выполняется через оператор пространства имен `::`.

```
utils::helper::greet("World")
```

## Переменные и константы

Объявляйте переменные с помощью `keep`.

```
keep message = "hello"
keep number = 5
```

Используйте `share keep`, чтобы экспортировать символ из модуля.

```
share keep global_var = 5
```

## Функции

Функции используют стрелочный синтаксис и могут быть общедоступными.

```
keep add = (a, b) => {
	return a + b
}

share keep main = () => {
	io::print("Hello")
}
```

### Возврат значений

Используйте `return` внутри блока.

```
keep getMessage = () => {
	return "hello world"
}
```

## Управление потоком

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

### Циклы

`go` итерирует списки.

```
keep lst = [1, "ok"]
go lst by x {
	io::print(x)
}
```

`stay` — это цикл, похожий на while.

```
keep i = 0
stay i < 5 {
	i += 1
}
```

### Диапазоны

Используйте `to`, чтобы создать список чисел в диапазоне.

```
keep range = 0 to 3 # создает [0, 1, 2]

go 0 to 3 by x {
	io::print(x) # печатает 0, 1, 2
}
```

## Классы и наследование

Классы объявляются с помощью `boy`.

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

Наследование использует `boy : Parent`.

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

Внутри переопределений вызывайте родителя через `daddy`.

## Создание объектов

Используйте `makeout`, чтобы создавать экземпляры.

```
keep h = makeout Human(18)
h.name = "Alex"
```

## Булевы значения и логика

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

## Списки

```
keep lst = [1, "okak"]
```

## Нативный код (JS Interop)

Пометьте переменную как native и присвойте значение внутри блока `native => { ... }`.

```
keep jsAlert = (message) => {
	keep result: native
	native => {
		result = String(message).toUpperCase()
	}
	return result
}
```

## Вариативные функции

Используйте `rest...`, чтобы собрать дополнительные аргументы.

```
keep varargFn = (first, rest...) => {
	io::print("First:", first)
	go rest by item {
		io::print("Rest item:", item)
	}
}
```

## Точка входа

Вызовите функцию `main` в конце файла.

```
main()
```
