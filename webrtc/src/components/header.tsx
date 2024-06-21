'use client'

import {useState} from 'react'
import styles from "@/styles/page.module.css";

interface HeaderProps {
    title: string
}

export default function Header(props: HeaderProps) {
    return (
        <div className={styles.header}>
        <h1>{props.title}</h1>
        </div>
    )
}

export function IncrementButton() {
    const [count, setCount] = useState(0)

    function handleClick() {
        console.log("Incrementing count")
        setCount(count + 1)
    }

    return (
        <button onClick={handleClick}>
            Press Me! Counting {count}
        </button>
    )
}