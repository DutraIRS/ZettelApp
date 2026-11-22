plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.chaquo.python")
}

android {
    namespace = "com.dutrairs.zettelapp"
    compileSdk = 35
    buildToolsVersion = "36.0.0"

    defaultConfig {
        applicationId = "com.dutrairs.zettelapp"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.3.1"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }
}

// Bundle the repo's Python package (zettelapp/…) into the APK. It is copied
// into a generated directory first: pointing chaquopy's srcDir at the repo
// root itself would make that directory a Gradle task input that contains
// other tasks' outputs, which Gradle 8 rejects (implicit dependency problem).
val pySrcDir = layout.buildDirectory.dir("generated/pythonSrc")
val bundlePython by tasks.registering(Copy::class) {
    from(layout.projectDirectory.dir("../.."))
    include("zettelapp/**")
    exclude("**/__pycache__/**", "**/*.pyc")
    into(pySrcDir)
}

chaquopy {
    defaultConfig {
        version = "3.12"
        pip {
            // Pure-Python dependencies of the core the mobile facade uses.
            // The heavy desktop wheels (PySide6, onnxruntime, numpy, rapidfuzz)
            // have no Android builds yet and stay out of the mobile app.
            install("markdown-it-py==4.2.0")
            install("PyYAML==6.0.3")
            install("genanki==0.13.1")
        }
    }
    sourceSets {
        getByName("main") {
            srcDir(pySrcDir)
        }
    }
}

afterEvaluate {
    tasks.matching { it.name.endsWith("PythonSources") }.configureEach {
        dependsOn(bundlePython)
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.activity:activity-compose:1.10.0")

    implementation(platform("androidx.compose:compose-bom:2025.01.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
}
