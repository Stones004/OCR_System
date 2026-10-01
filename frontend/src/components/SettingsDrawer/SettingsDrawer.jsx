import "./SettingsDrawer.css"

import {
    useEffect,
    useState
} from "react"

function SettingsDrawer({

    open,

    onClose
}) {

    const [

        settings,

        setSettings

    ] = useState(null)

    const [expandedSections, setExpandedSections] =
        useState({

            runtime: false,

            output: false,

            validation: false,

            geometry: false,

            blur: false,

            skew: false,

            brightness: false,

            contrast: false,

            content_density: false,

            edge_density: false,

            scoring: false,

            document_geometry: false,

            image_quality: false,

            content_analysis: false
        })

    useEffect(() => {

        if (!open) {

            return
        }

        fetch("/config")

            .then(

                res => res.json()
            )

            .then(

                data => {

                    setSettings(
                        data
                    )
                }
            )

            .catch(

                console.error
            )

    }, [open])

    const saveSettings =
        async () => {

            try {

                await fetch(

                    "/config",

                    {

                        method:
                            "PATCH",

                        headers: {

                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                settings
                            )
                    }
                )

                showToast(
                    "Settings saved successfully",
                    "success"
                )

            } catch (err) {

                console.error(
                    err
                )

                alert(
                    "Failed to Save"
                )
            }
        }

    if (!settings) {

        return (

            <div
                className={
                    open
                        ? "drawer open"
                        : "drawer"
                }
            >

                <div className="drawer-header">

                    Settings

                    <button
                        onClick={
                            onClose
                        }
                    >

                        X

                    </button>

                </div>

                <div className="drawer-content">

                    Loading...

                </div>

            </div>
        )
    }

    const toggleSection = section => {

        setExpandedSections(

            prev => ({

                ...prev,

                [section]:
                    !prev[section]
            })
        )
    }

    const thresholdGroups = {

        document_geometry: [
            "geometry",
            "skew"
        ],

        image_quality: [
            "blur",
            "brightness",
            "contrast"
        ],

        content_analysis: [
            "content_density",
            "edge_density"
        ],

        scoring: [
            "scoring"
        ]
    }

    return (

        <div
            className={
                open
                    ? "drawer open"
                    : "drawer"
            }
        >

            <div className="drawer-header">

                Settings

                <button
                    className="close-btn"
                    onClick={onClose}
                >

                    ✕

                </button>

            </div>

            <div className="drawer-content">

                {/* Runtime */}

                <div className="settings-card">

                    <div
                        className="threshold-header"
                        onClick={() => toggleSection("runtime")}
                    >

                        <span
                            className={
                                expandedSections.runtime
                                    ? "dropdown-arrow expanded"
                                    : "dropdown-arrow"
                            }
                        >
                            ▶
                        </span>

                        Runtime

                    </div>

                    {expandedSections.runtime && (

                        <label>

                            Device

                            <select
                                value={
                                    settings.runtime?.preferred_device
                                }
                                onChange={e =>
                                    setSettings(prev => ({
                                        ...prev,
                                        runtime: {
                                            ...prev.runtime,
                                            preferred_device:
                                                e.target.value
                                        }
                                    }))
                                }
                            >

                                <option value="cpu">
                                    CPU
                                </option>

                                <option value="cuda">
                                    CUDA
                                </option>

                            </select>

                        </label>

                    )}

                </div>

                {/* Output */}

                <div className="settings-card">

                    <div
                        className="threshold-header"
                        onClick={() => toggleSection("output")}
                    >

                        <span
                            className={
                                expandedSections.output
                                    ? "dropdown-arrow expanded"
                                    : "dropdown-arrow"
                            }
                        >
                            ▶
                        </span>

                        Output

                    </div>

                    {expandedSections.output && (

                        <>

                            <label>

                                Save Exports

                                <input
                                    type="checkbox"
                                    checked={
                                        settings.output?.save_exports
                                    }
                                    onChange={e =>
                                        setSettings(prev => ({
                                            ...prev,
                                            output: {
                                                ...prev.output,
                                                save_exports:
                                                    e.target.checked
                                            }
                                        }))
                                    }
                                />

                            </label>

                            <label>

                                Save Visualizations

                                <input
                                    type="checkbox"
                                    checked={
                                        settings.output?.save_visualizations
                                    }
                                    onChange={e =>
                                        setSettings(prev => ({
                                            ...prev,
                                            output: {
                                                ...prev.output,
                                                save_visualizations:
                                                    e.target.checked
                                            }
                                        }))
                                    }
                                />

                            </label>

                        </>

                    )}

                </div>

                {/* Validation */}

                <div className="settings-section-title">

                    ADVANCED CONFIGURATION

                </div>

                <div className="settings-card">

                    <div
                        className="threshold-header validation-title"
                        onClick={() => toggleSection("validation")}
                    >

                        <span
                            className={
                                expandedSections.validation
                                    ? "dropdown-arrow expanded"
                                    : "dropdown-arrow"
                            }
                        >
                            ▶
                        </span>

                        Validation Thresholds

                    </div>

                    {
                        expandedSections.validation &&

                        Object.entries(thresholdGroups).map(

                            ([groupName, sections]) => (

                                <div
                                    key={groupName}
                                    className="threshold-group"
                                >

                                    <div

                                        className="threshold-header group-header"

                                        onClick={() =>
                                            toggleSection(groupName)
                                        }
                                    >

                                        <span
                                            className={
                                                expandedSections[groupName]

                                                    ?

                                                    "dropdown-arrow expanded"

                                                    :

                                                    "dropdown-arrow"
                                            }
                                        >
                                            ▶
                                        </span>

                                        {
                                            groupName
                                                .replaceAll("_", " ")
                                                .replace(
                                                    /\b\w/g,
                                                    c => c.toUpperCase()
                                                )
                                        }

                                    </div>

                                    {

                                        expandedSections[groupName] &&

                                        sections.map(section => {

                                            const values =
                                                settings.thresholds?.[section]

                                            if (!values) {

                                                return null
                                            }

                                            return (

                                                <div
                                                    key={section}
                                                    className="threshold-section"
                                                >

                                                    <div

                                                        className="threshold-header"

                                                        onClick={() =>
                                                            toggleSection(section)
                                                        }
                                                    >

                                                        <span
                                                            className={
                                                                expandedSections[section]

                                                                    ?

                                                                    "dropdown-arrow expanded"

                                                                    :

                                                                    "dropdown-arrow"
                                                            }
                                                        >
                                                            ▶
                                                        </span>

                                                        {
                                                            section
                                                                .replaceAll("_", " ")
                                                                .replace(
                                                                    /\b\w/g,
                                                                    c => c.toUpperCase()
                                                                )
                                                        }

                                                        <span
                                                            className="rule-count"
                                                        >

                                                            {
                                                                Object.keys(values).length
                                                            }

                                                            {" "}
                                                            rules

                                                        </span>

                                                    </div>

                                                    {

                                                        expandedSections[section] &&

                                                        Object.entries(values).map(

                                                            ([key, value]) => (

                                                                <div
                                                                    key={`${section}-${key}`}
                                                                    className="setting-row"
                                                                >

                                                                    <label>

                                                                        {
                                                                            key
                                                                                .replaceAll("_", " ")
                                                                                .replace(
                                                                                    /\b\w/g,
                                                                                    c => c.toUpperCase()
                                                                                )
                                                                        }

                                                                    </label>

                                                                    <input
                                                                        type="number"
                                                                        step="0.01"
                                                                        value={value}
                                                                        onChange={e =>
                                                                            setSettings(
                                                                                prev => ({
                                                                                    ...prev,
                                                                                    thresholds: {
                                                                                        ...prev.thresholds,
                                                                                        [section]: {
                                                                                            ...prev.thresholds[section],
                                                                                            [key]:
                                                                                                parseFloat(
                                                                                                    e.target.value
                                                                                                )
                                                                                        }
                                                                                    }
                                                                                })
                                                                            )
                                                                        }
                                                                    />

                                                                </div>

                                                            )
                                                        )

                                                    }

                                                </div>
                                            )
                                        })

                                    }

                                </div>
                            )
                        )
                    }

                </div>

                <button
                    className="save-settings-btn"
                    onClick={saveSettings}
                >

                    Save Settings

                </button>

            </div>


        </div>
    )
}

export default SettingsDrawer