import OverlayViewer from "../OverlayViewer/OverlayViewer"

import "./Viewer.css"
import BookletDetails from
    "../BookletDetails/BookletDetails"

import {
    useState,
    useEffect,
    useMemo
} from "react"

function Viewer({

    selectedPage,

    selectedBooklet,

    setSelectedPage,

    updateBookletStatus
}) {

    const [showQuestions, setShowQuestions] =
        useState(true)

    const [showSummary, setShowSummary] =
        useState(false)

    const [selectedQuestion, setSelectedQuestion] =
        useState(null)

    useEffect(() => {

        setSelectedQuestion(null)

    }, [selectedBooklet?.id])

    const questions =

        selectedPage
            ?.payload
            ?.omr_result
            ?.questions || []

    const labelCount =

        questions.filter(
            q => !q.is_continuation
        ).length

    const continuationCount =

        questions.filter(
            q => q.is_continuation
        ).length

    const missingLookupCount =

        questions.filter(

            q =>
                !q.is_continuation &&
                !q.lookup_tag

        ).length

    // One row per unique instance_id across the whole booklet, with every
    // page that answer appears on (its label page plus any continuation
    // pages) -- replaces the original's bubble-band range computation,
    // since answer_bbox already carries the real extent directly.
    //
    // Grouped by instance_id, NOT question_id: question_id is just the
    // label's literal OCR text, so two unrelated "1" labels share it --
    // grouping by text would wrongly merge two different answers into one
    // row. instance_id is the backend's per-detection unique id (see
    // app/engine/models.py's Annotation docstring).
    const questionGroups = useMemo(() => {

        const groups = {}

        selectedBooklet?.pages?.forEach(page => {

            (page.payload?.omr_result?.questions || []).forEach(q => {

                if (!groups[q.instance_id]) {

                    groups[q.instance_id] = {
                        instance_id: q.instance_id,
                        question_id: q.question_id,
                        text: q.text,
                        lookup_tag: q.lookup_tag,
                        pages: []
                    }
                }

                groups[q.instance_id].pages.push(page.page_number)

                if (q.lookup_tag) {
                    groups[q.instance_id].lookup_tag = q.lookup_tag
                }
            })
        })

        return Object.values(groups)

    }, [selectedBooklet])

    const selectQuestionGroup = (group) => {

        setSelectedQuestion({ instance_id: group.instance_id })

        const firstPageNumber = group.pages[0]

        const page = selectedBooklet.pages.find(
            p => p.page_number === firstPageNumber
        )

        if (page) {
            setSelectedPage(page)
        }
    }

    return (

        <div className="viewer">

            {

                selectedBooklet && (

                    <div className="viewer-header">

                        <div className="viewer-header-content">

                            <div className="viewer-header-left">

                                <div className="viewer-header-label">

                                    Assessment Batch

                                </div>

                                <div className="viewer-header-title">

                                    {selectedBooklet.name}

                                </div>

                            </div>

                            <div className="viewer-header-right">

                                <div
                                    className={`viewer-status-badge status-${selectedBooklet.status?.toLowerCase()}`}
                                >

                                    {selectedBooklet.status}

                                </div>

                                <div className="viewer-page-badge">

                                    Page {selectedPage?.page_number}

                                    {" / "}

                                    {selectedBooklet.pages.length}

                                </div>

                            </div>

                        </div>

                    </div>
                )
            }

            <div className="viewer-layout">

                <div className="image-section">

                    <OverlayViewer

                        selectedPage={selectedPage}

                        selectedBooklet={selectedBooklet}

                        setSelectedPage={
                            setSelectedPage
                        }

                        selectedQuestion={
                            selectedQuestion
                        }

                        setSelectedQuestion={
                            setSelectedQuestion
                        }
                    />

                </div>

                <div className="metadata-section">

                    <h3>

                        Metadata

                    </h3>

                    <hr />

                    <div className="metadata-content">

                        <BookletDetails

                            selectedBooklet={
                                selectedBooklet
                            }

                            updateBookletStatus={
                                updateBookletStatus
                            }
                        />

                        <div className="details-card">

                            <div
                                className="section-header"
                                onClick={() =>
                                    setShowSummary(
                                        !showSummary
                                    )
                                }
                            >

                                <span
                                    className={
                                        showSummary
                                            ? "dropdown-arrow expanded"
                                            : "dropdown-arrow"
                                    }
                                >

                                    ▶

                                </span>

                                Annotation Summary

                            </div>

                            {

                                showSummary && (

                                    <>

                                        <div className="metric-row">

                                            <span>

                                                Question Labels

                                            </span>

                                            <strong>

                                                {labelCount}

                                            </strong>

                                        </div>

                                        <div className="metric-row">

                                            <span>

                                                Continuation Rows

                                            </span>

                                            <strong>

                                                {continuationCount}

                                            </strong>

                                        </div>

                                        <div className="metric-row">

                                            <span>

                                                Missing lookup_tag

                                            </span>

                                            <strong>

                                                {missingLookupCount}

                                            </strong>

                                        </div>

                                    </>
                                )
                            }

                        </div>

                        <div className="details-card">

                            <div
                                className="section-header"
                                onClick={() =>
                                    setShowQuestions(
                                        !showQuestions
                                    )
                                }
                            >

                                <span
                                    className={
                                        showQuestions
                                            ? "dropdown-arrow expanded"
                                            : "dropdown-arrow"
                                    }
                                >

                                    ▶

                                </span>

                                Questions

                                <span className="question-count">

                                    (
                                    {questionGroups.length}
                                    )

                                </span>

                            </div>

                            {

                                showQuestions && (

                                    questionGroups.length === 0

                                        ?
                                        (
                                            <div>
                                                No Questions
                                            </div>
                                        )

                                        :
                                        (
                                            questionGroups.map(

                                                group => (

                                                    <div

                                                        key={
                                                            `${selectedBooklet.name}-${group.instance_id}`
                                                        }

                                                        className={

                                                            selectedQuestion
                                                                ?.instance_id ===

                                                                group.instance_id

                                                                ?

                                                                "question-item selected"

                                                                :

                                                                "question-item"
                                                        }

                                                        onClick={() =>
                                                            selectQuestionGroup(group)
                                                        }

                                                    >

                                                        {group.lookup_tag || group.question_id}

                                                        {
                                                            !group.lookup_tag &&
                                                            " ⚠"
                                                        }

                                                        {" "}

                                                        (P{group.pages[0]}
                                                        {
                                                            group.pages.length > 1 &&
                                                            `-P${group.pages[group.pages.length - 1]}`
                                                        }
                                                        )

                                                    </div>
                                                )
                                            )
                                        )
                                )
                            }

                        </div>
                    </div>

                </div>

            </div>

        </div>
    )
}

export default Viewer
