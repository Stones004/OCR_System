import "./BookletDetails.css"
import { useState } from "react"

function BookletDetails({

    selectedBooklet,
    updateBookletStatus

}) {

    const [showActions, setShowActions] =
        useState(false)

    const [showReasons, setShowReasons] =
        useState(false)

    if (!selectedBooklet) {

        return (

            <div className="details-panel">

                <p>Select a booklet</p>

            </div>

        )

    }

    const status =
        selectedBooklet.status ?? "REVIEW"

    const sendToRescan =
        async () => {

            const response =
                await fetch(

                    `/jobs/${selectedBooklet.jobId}/rescan`,

                    {
                        method: "POST"
                    }
                )

            if (!response.ok) {

                alert("Failed to move PDF")

                return

            }

            updateBookletStatus(

                selectedBooklet.jobId,

                selectedBooklet.id,

                "RESCAN"

            )

        }

    return (

        <div className="details-panel">

            <div className="overview-card">

                <div className="card-label">

                    Assessment Batch

                </div>

                <div className="booklet-name">

                    {selectedBooklet.id}

                </div>

                <div className="overview-footer">

                    <div
                        className={`status-badge status-${status.toLowerCase()}`}
                    >
                        {status}
                    </div>

                    <div className="page-count">

                        {selectedBooklet.pages.length}
                        {" "}
                        Pages

                    </div>

                </div>

            </div>

            <div className="details-card">

                <div
                    className="section-header"
                    onClick={() =>
                        setShowReasons(
                            !showReasons
                        )
                    }
                >

                    <span
                        className={
                            showReasons
                                ? "dropdown-arrow expanded"
                                : "dropdown-arrow"
                        }
                    >

                        ▶

                    </span>

                    Review Reasons

                </div>

                {

                    showReasons && (

                        <div className="section-content">

                            {
                                selectedBooklet.reasons?.length

                                    ?

                                    selectedBooklet.reasons.map(

                                        (reason, idx) => (

                                            <div
                                                key={idx}
                                                className="reason-item"
                                            >
                                                • {reason}
                                            </div>
                                        )
                                    )

                                    :

                                    <div className="empty-reason">

                                        No review reasons

                                    </div>
                            }

                        </div>
                    )
                }

            </div>

            <div className="details-card">

                <div
                    className="section-header"
                    onClick={() =>
                        setShowActions(
                            !showActions
                        )
                    }
                >

                    <span
                        className={
                            showActions
                                ? "dropdown-arrow expanded"
                                : "dropdown-arrow"
                        }
                    >

                        ▶

                    </span>

                    Workflow Actions

                </div>

                {
                    showActions && (

                        <div className="workflow-actions">

                            <button
                                className="workflow-btn pass-btn"
                                onClick={() =>
                                    updateBookletStatus(

                                        selectedBooklet.jobId,

                                        selectedBooklet.id,

                                        "PASS"

                                    )
                                }
                            >

                                ✓ Mark as Pass

                            </button>

                            <button
                                className="workflow-btn review-btn"
                                onClick={() =>
                                    updateBookletStatus(

                                        selectedBooklet.jobId,

                                        selectedBooklet.id,

                                        "REVIEW"

                                    )
                                }
                            >

                                ⚠ Needs Review

                            </button>

                            <button
                                className="workflow-btn rescan-btn"
                                onClick={sendToRescan}
                            >

                                ↻ Send To Rescan

                            </button>

                        </div>
                    )
                }

            </div>

        </div>
    )
}

export default BookletDetails