import "./PageTree.css"
import { useState } from "react"

function PageTree({
    booklets,
    setSelectedPage,
    setSelectedBooklet,
    selectedPage
}) {


    const [expandedGroups, setExpandedGroups] =
        useState({
            PASS: true,
            REVIEW: true,
            RESCAN: true
        })

    const [expandedBooklets, setExpandedBooklets] =
        useState({})

    const passBooklets = []
    const reviewBooklets = []
    const rescanBooklets = []

    Object.entries(booklets).forEach(([id, booklet]) => {

        if (!booklet.current_session) {
            return
        }

        switch (booklet.status) {

            case "PASS":
                passBooklets.push([id, booklet])
                break

            case "REVIEW":
                reviewBooklets.push([id, booklet])
                break

            case "RESCAN":
                rescanBooklets.push([id, booklet])
                break

            default:
                reviewBooklets.push([id, booklet])
        }

    })

    const renderBooklets = (
        title,
        statusKey,
        items
    ) => (

        <div className="status-group">

            <div

                className={`status-header status-${statusKey.toLowerCase()}`}

                onClick={() =>

                    setExpandedGroups(prev => ({
                        ...prev,
                        [statusKey]:
                            !prev[statusKey]
                    }))
                }
            >

                <span
                    className={
                        expandedGroups[statusKey]
                            ? "dropdown-arrow expanded"
                            : "dropdown-arrow"
                    }
                >
                    ▶
                </span>

                <div className="status-title">
                    {title}
                </div>

                <div className="status-count">
                    {items.length}
                </div>

            </div>

            <div
                className={
                    expandedGroups[statusKey]
                        ? "status-content open"
                        : "status-content"
                }
            >

                {
                    items.length === 0 && (

                        <div className="empty-group">
                            No booklets available
                        </div>
                    )
                }

                {
                    items.map(
                        ([bookletId, booklet]) => (

                            <div
                                key={bookletId}
                                className="booklet-card"
                            >

                                <div

                                    className="booklet-header"

                                    onClick={() => {

                                        setSelectedBooklet({
                                            ...booklet
                                        })

                                        setExpandedBooklets(
                                            prev => ({
                                                ...prev,
                                                [bookletId]:
                                                    !prev[bookletId]
                                            })
                                        )
                                    }}
                                >

                                    <div className="booklet-left">

                                        <div
                                            className={
                                                expandedBooklets[bookletId]
                                                    ? "booklet-expand expanded"
                                                    : "booklet-expand"
                                            }
                                        >
                                            ▶
                                        </div>

                                        <div className="booklet-info">

                                            <div className="booklet-title">
                                                Assessment Batch
                                            </div>

                                            <div className="booklet-id">
                                                {booklet.name}
                                            </div>

                                        </div>

                                    </div>

                                    <div className="booklet-pages">
                                        {booklet.pages.length} Pages
                                    </div>

                                </div>

                                {
                                    booklet.reasons?.map(
                                        (reason, idx) => (

                                            <div
                                                key={idx}
                                                className="reason"
                                            >
                                                • {reason}
                                            </div>
                                        )
                                    )
                                }

                                <div
                                    className={
                                        expandedBooklets[bookletId]
                                            ? "booklet-content open"
                                            : "booklet-content"
                                    }
                                >

                                    <div className="page-grid">

                                        {
                                            booklet.pages.map(
                                                (page, idx) => (

                                                    <button

                                                        key={idx}

                                                        className={
                                                            selectedPage?.page_number ===
                                                                page.page_number
                                                                ? "page-chip active"
                                                                : "page-chip"
                                                        }

                                                        onClick={() => {

                                                            setSelectedPage(page)

                                                            setSelectedBooklet({
                                                                ...booklet
                                                            })
                                                        }}
                                                    >

                                                        P{page.page_number}

                                                    </button>
                                                )
                                            )
                                        }

                                    </div>

                                </div>

                            </div>
                        )
                    )
                }

            </div>

        </div>
    )

    return (

        <div className="page-tree">

            {
                renderBooklets(
                    "Passed",
                    "PASS",
                    passBooklets
                )
            }

            {
                renderBooklets(
                    "Needs Review",
                    "REVIEW",
                    reviewBooklets
                )
            }

            {
                renderBooklets(
                    "Needs Rescan",
                    "RESCAN",
                    rescanBooklets
                )
            }

        </div>
    )


}

export default PageTree
