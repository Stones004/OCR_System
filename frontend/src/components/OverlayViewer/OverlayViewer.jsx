import { useState } from "react"

import "./OverlayViewer.css"

import {
    useRef,
    useEffect
} from "react"

// Colours match app/core/config/config.yaml's visualization.class_colors
// (BGR there, RGB/hex here) so the live browser view and the saved debug
// PNGs agree.
const LABEL_COLOR = "#FF3B30"
const ANSWER_COLOR = "#22C55E"
const CONTINUATION_COLOR = "#F5A623"
const SELECTED_COLOR = "#FFD400"

function OverlayViewer({

    selectedPage,

    selectedBooklet,

    setSelectedPage,

    selectedQuestion,

    setSelectedQuestion
}) {
    const [zoom, setZoom] =
        useState(1)

    const [showLabels, setShowLabels] =
        useState(true)

    const [showAnswers, setShowAnswers] =
        useState(true)

    const [showContinuations, setShowContinuations] =
        useState(true)

    const scrollRef = useRef(null)

    const pageRefs = useRef({})

    const programmaticScroll =
        useRef(false)

    useEffect(() => {
        if (

            !selectedBooklet ||
            !setSelectedPage
        ) {
            return

        }

        const observer =
            new IntersectionObserver(
                (entries) => {
                    entries.forEach(

                        (entry) => {
                            if (
                                entry.isIntersecting
                            ) {
                                const pageNum =
                                    Number(
                                        entry.target.dataset.page

                                    )
                                const page =
                                    selectedBooklet.pages.find(
                                        p =>
                                            p.page_number === pageNum

                                    )

                                if (
                                    page &&
                                    !programmaticScroll.current
                                ) {
                                    setSelectedPage(
                                        page

                                    )

                                }

                            }

                        }

                    )

                },
                {
                    threshold: 0.6
                }

            )

        Object.values(
            pageRefs.current
        ).forEach(
            el => {
                if (el)
                    observer.observe(el)
            }

        )
        return () =>
            observer.disconnect()
    }, [
        selectedBooklet,
        setSelectedPage

    ])

    useEffect(() => {

        if (

            !selectedPage

        ) {

            return
        }

        programmaticScroll.current =
            true

        const element =

            document.getElementById(

                `page-${selectedPage.page_number}`
            )

        if (

            element

        ) {

            element.scrollIntoView({

                behavior: "smooth",

                block: "start"
            })
        }

        setTimeout(() => {

            programmaticScroll.current =
                false

        }, 500)

    }, [

        selectedPage

    ])


    const handleWheel = (e) => {

        if (

            !e.ctrlKey

        ) {

            return
        }

        e.preventDefault()

        const scaleFactor =

            e.deltaY < 0

                ? 1.1

                : 0.9

        setZoom(prev =>

            Math.min(

                3,

                Math.max(

                    0.25,

                    prev *
                    scaleFactor
                )
            )
        )
    }

    const zoomLevels = [

        0.25,
        0.5,
        0.75,
        1,
        1.25,
        1.5,
        2,
        3
    ]

    const zoomIn = () => {

        const currentIndex =

            zoomLevels.findIndex(

                z => z >= zoom
            )

        if (

            currentIndex <
            zoomLevels.length - 1

        ) {

            setZoom(

                zoomLevels[
                currentIndex + 1
                ]
            )
        }
    }


    const zoomOut = () => {

        const currentIndex =

            zoomLevels.findIndex(

                z => z >= zoom
            )

        if (

            currentIndex > 0

        ) {

            setZoom(

                zoomLevels[
                currentIndex - 1
                ]
            )
        }
    }

    if (

        !selectedBooklet ||

        !selectedBooklet.pages

    ) {

        return (

            <div className="empty-viewer">

                Select a Booklet

            </div>
        )
    }

    const apiHost =

        window.location.port === "5173"

            ? `${window.location.hostname}:8000`

            : window.location.host

    const fitWidth = () => {

        if (

            !scrollRef.current ||

            !selectedBooklet?.pages?.length

        ) return

        const viewerWidth =

            scrollRef.current.clientWidth

        const firstPage =

            selectedBooklet.pages[0]

        const imageWidth =
            firstPage.payload?.prediction_result?.image_width ??
            firstPage.image_width

        if (!imageWidth) return

        const scale =
            (viewerWidth - 50) /
            imageWidth

        setZoom(scale)

        requestAnimationFrame(() => {

            scrollRef.current.scrollTo({

                top: 0,

                behavior: "smooth"
            })
        })
    }

    const fitPage = () => {

        if (
            !scrollRef.current ||
            !selectedBooklet?.pages?.length
        ) {
            return
        }

        const firstPage = selectedBooklet.pages[0]

        const imageWidth =
            firstPage.payload?.prediction_result?.image_width ??
            firstPage.image_width

        const imageHeight =
            firstPage.payload?.prediction_result?.image_height ??
            firstPage.image_height

        if (!imageWidth || !imageHeight) {

            console.error(
                "Missing image dimensions",
                firstPage
            )

            return
        }

        const availableWidth =
            scrollRef.current.clientWidth - 50

        const availableHeight =
            scrollRef.current.clientHeight - 50

        const widthScale =
            availableWidth / imageWidth

        const heightScale =
            availableHeight / imageHeight

        setZoom(Math.min(widthScale, heightScale))

        requestAnimationFrame(() => {

            scrollRef.current.scrollTo({
                top: 0,
                behavior: "smooth"
            })

        })

    }

    return (

        <div className="document-viewer">

            <div className="viewer-toolbar">

                <button
                    onClick={fitPage}
                >
                    Fit Page
                </button>

                <button
                    onClick={fitWidth}
                >
                    Fit Width
                </button>

                <button
                    onClick={zoomIn}
                >
                    +
                </button>

                <span>

                    {Math.round(
                        zoom * 100
                    )}%

                </span>

                <button

                    onClick={zoomOut}
                >
                    -
                </button>

                <select

                    value={zoom}

                    onChange={(e) =>

                        setZoom(
                            Number(
                                e.target.value
                            )
                        )
                    }
                >

                    {

                        zoomLevels.map(

                            level => (

                                <option

                                    key={level}

                                    value={level}
                                >

                                    {

                                        Math.round(
                                            level * 100
                                        )

                                    }%

                                </option>
                            )
                        )
                    }

                </select>

                <label>

                    <input

                        type="checkbox"

                        checked={showLabels}

                        onChange={() =>
                            setShowLabels(
                                !showLabels
                            )
                        }
                    />

                    Question Labels

                </label>

                <label>

                    <input

                        type="checkbox"

                        checked={showAnswers}

                        onChange={() =>
                            setShowAnswers(
                                !showAnswers
                            )
                        }
                    />

                    Answer Regions

                </label>

                <label>

                    <input

                        type="checkbox"

                        checked={showContinuations}

                        onChange={() =>
                            setShowContinuations(
                                !showContinuations
                            )
                        }
                    />

                    Continuations

                </label>

            </div>

            <div

                ref={scrollRef}

                className="document-scroll"

                onWheel={handleWheel}
            >

                {

                    selectedBooklet.pages.map(

                        (page) => {

                            const imageUrl =
                                `${window.location.protocol}//${apiHost}/images/${page.image_path}`

                            const questions =

                                page.payload
                                    ?.omr_result
                                    ?.questions || []

                            const visibleQuestions =

                                questions.filter(q => {

                                    if (
                                        q.is_continuation &&
                                        !showContinuations
                                    ) {
                                        return false
                                    }

                                    return true
                                })

                            const imageWidth =

                                page.payload
                                    ?.prediction_result
                                    ?.image_width

                                ||

                                page.image_width

                            const imageHeight =

                                page.payload
                                    ?.prediction_result
                                    ?.image_height

                                ||

                                page.image_height


                            return (

                                <div

                                    key={
                                        page.page_number
                                    }

                                    id={
                                        `page-${page.page_number}`
                                    }

                                    data-page={
                                        page.page_number
                                    }

                                    ref={(el) =>

                                        pageRefs.current[
                                        page.page_number
                                        ] = el
                                    }

                                    className="booklet-page"
                                >

                                    <div

                                        className="page-container"

                                        style={{

                                            width:
                                                imageWidth *
                                                zoom,

                                            height:
                                                imageHeight *
                                                zoom
                                        }}

                                    >

                                        <div className="page-badge">

                                            Page {page.page_number}

                                        </div>

                                        <img

                                            src={imageUrl}

                                            alt="page"

                                            className="page-image"

                                            style={{

                                                width:
                                                    imageWidth *
                                                    zoom,

                                                height:
                                                    imageHeight *
                                                    zoom
                                            }}
                                        />

                                        <svg

                                            className="overlay-svg"

                                            width={
                                                imageWidth *
                                                zoom
                                            }

                                            height={
                                                imageHeight *
                                                zoom
                                            }
                                        >

                                            {

                                                visibleQuestions.map(

                                                    (q, idx) => {

                                                        const isSelected =

                                                            selectedQuestion?.instance_id ===
                                                            q.instance_id

                                                        const labelColor =

                                                            isSelected
                                                                ? SELECTED_COLOR
                                                                : q.is_continuation
                                                                    ? CONTINUATION_COLOR
                                                                    : LABEL_COLOR

                                                        return (

                                                            <g
                                                                key={
                                                                    `${page.page_number}-${idx}`
                                                                }

                                                                onClick={() =>

                                                                    setSelectedQuestion?.(q)
                                                                }

                                                                style={{
                                                                    cursor: "pointer",
                                                                    pointerEvents: "all"
                                                                }}
                                                            >

                                                                {

                                                                    showAnswers &&
                                                                    q.answer_bbox &&
                                                                    (() => {

                                                                        const [
                                                                            ax1, ay1, ax2, ay2
                                                                        ] = q.answer_bbox

                                                                        return (

                                                                            <rect

                                                                                x={ax1 * zoom}

                                                                                y={ay1 * zoom}

                                                                                width={(ax2 - ax1) * zoom}

                                                                                height={(ay2 - ay1) * zoom}

                                                                                fill={
                                                                                    isSelected
                                                                                        ? "rgba(255,212,0,0.15)"
                                                                                        : "rgba(34,197,94,0.06)"
                                                                                }

                                                                                stroke={
                                                                                    isSelected
                                                                                        ? SELECTED_COLOR
                                                                                        : ANSWER_COLOR
                                                                                }

                                                                                strokeWidth={
                                                                                    isSelected ? 3 : 1.5
                                                                                }
                                                                            />
                                                                        )
                                                                    })()
                                                                }

                                                                {

                                                                    showLabels &&
                                                                    q.question_bbox &&
                                                                    (() => {

                                                                        const [
                                                                            x1, y1, x2, y2
                                                                        ] = q.question_bbox

                                                                        const label =

                                                                            q.lookup_tag ||
                                                                            q.question_id

                                                                        return (

                                                                            <>
                                                                                <rect

                                                                                    x={x1 * zoom}

                                                                                    y={y1 * zoom}

                                                                                    width={(x2 - x1) * zoom}

                                                                                    height={(y2 - y1) * zoom}

                                                                                    fill="none"

                                                                                    stroke={labelColor}

                                                                                    strokeWidth={
                                                                                        isSelected ? 4 : 3
                                                                                    }
                                                                                />

                                                                                <text

                                                                                    x={x1 * zoom}

                                                                                    y={(y1 - 8) * zoom}

                                                                                    fill={labelColor}

                                                                                    fontWeight="bold"
                                                                                >

                                                                                    {label}

                                                                                    {
                                                                                        !q.lookup_tag &&
                                                                                        " ⚠"
                                                                                    }

                                                                                </text>
                                                                            </>
                                                                        )
                                                                    })()
                                                                }

                                                            </g>
                                                        )
                                                    }
                                                )
                                            }

                                        </svg>

                                    </div>

                                </div>
                            )
                        }
                    )
                }

            </div>

        </div>
    )
}

export default OverlayViewer
